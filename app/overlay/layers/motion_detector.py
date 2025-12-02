"""Слой детектора движения."""

import asyncio
import concurrent.futures
import logging

import cv2
import numpy as np

from app.overlay.layers.base import Layer
from app.overlay.motion.grid_utils import calculate_cell_size, get_cell_bounds
from app.overlay.plugin_registry import register_layer

logger = logging.getLogger(__name__)


@register_layer("motion_detector")
class MotionDetectorLayer(Layer):
    """
    Слой детектора движения с визуализацией.

    ЭТАП 1: Отрисовка сетки для проверки разбиения кадра на ячейки.
    ЭТАП 2: Детекция движения и визуализация квадратиков.
    """

    def __init__(
        self,
        enabled: bool = True,
        stage: int = 1,
        # Параметры сетки
        grid_width: int = 24,
        grid_height: int = 18,
        # Детекция (stage 2)
        algorithm: str = "grid_mean",
        threshold: float = 25.0,
        alpha: float = 0.02,
        alpha_fast_multiplier: float = 5.0,
        alpha_slow_multiplier: float = 0.5,
        use_adaptive_threshold: bool = True,
        min_brightness: float = 10.0,
        max_change_threshold: float = 200.0,
        # Производительность
        max_detection_fps: int = 15,
        skip_frames: int = 0,
        enable_profiling: bool = True,
        show_performance: bool = True,
        # Визуализация движения (stage 2)
        box_color: tuple[int, int, int] = (0, 255, 0),
        box_thickness: int = 2,
        box_fill_alpha: float = 0.3,
        # Визуализация сетки (stage 1)
        show_grid_lines: bool = True,
        grid_line_color: tuple[int, int, int] = (0, 255, 0),
        grid_line_thickness: int = 1,
        grid_line_alpha: float = 0.5,
        # UI
        show_cell_info: bool = False,
        show_stats: bool = True,
    ) -> None:
        """
        Инициализация слоя детектора движения.

        Args:
            enabled: Включён ли слой
            stage: Этап реализации (1 = сетка, 2 = детекция)
            grid_width: Количество столбцов сетки
            grid_height: Количество строк сетки
            algorithm: Алгоритм детекции ("grid_mean" | "grid_rms")
            threshold: Базовый порог детекции движения
            alpha: Базовая скорость обновления фона
            alpha_fast_multiplier: Множитель для быстрого обновления (нет движения)
            alpha_slow_multiplier: Множитель для медленного обновления (есть движение)
            use_adaptive_threshold: Использовать адаптивный порог на основе std
            min_brightness: Минимальная средняя яркость для детекции
            max_change_threshold: Порог для определения резкого изменения освещения
            max_detection_fps: Максимальный FPS детекции (0 = без ограничений)
            skip_frames: Пропускать N кадров между детекциями
            enable_profiling: Включить профилирование производительности
            show_performance: Показывать статистику производительности
            box_color: Цвет квадратиков с движением
            box_thickness: Толщина рамки квадратиков
            box_fill_alpha: Прозрачность заливки квадратиков
            show_grid_lines: Показывать линии сетки
            grid_line_color: Цвет линий сетки (RGB)
            grid_line_thickness: Толщина линий сетки
            grid_line_alpha: Прозрачность линий сетки
            show_cell_info: Показывать номера ячеек (для отладки)
            show_stats: Показывать информацию о сетке
        """
        super().__init__(enabled, priority=Layer.PRIORITY_BACKGROUND)

        self.stage = stage

        # Параметры сетки
        self.grid_width = grid_width
        self.grid_height = grid_height

        # Детекция (stage 2)
        self.algorithm = algorithm
        self.threshold = threshold
        self.alpha = alpha
        self.alpha_fast_multiplier = alpha_fast_multiplier
        self.alpha_slow_multiplier = alpha_slow_multiplier
        self.use_adaptive_threshold = use_adaptive_threshold
        self.min_brightness = min_brightness
        self.max_change_threshold = max_change_threshold

        # Производительность
        self.max_detection_fps = max_detection_fps
        self.skip_frames = skip_frames
        self.enable_profiling = enable_profiling
        self.show_performance = show_performance

        # Визуализация движения
        self.box_color = tuple(box_color)
        self.box_thickness = box_thickness
        self.box_fill_alpha = box_fill_alpha

        # Визуализация сетки
        self.show_grid_lines = show_grid_lines
        self.grid_line_color = tuple(grid_line_color)
        self.grid_line_thickness = grid_line_thickness
        self.grid_line_alpha = grid_line_alpha

        # UI
        self.show_cell_info = show_cell_info
        self.show_stats = show_stats

        self.font = cv2.FONT_HERSHEY_SIMPLEX

        # Детектор (только для stage 2)
        self.detector = None
        self.motion_matrix = None
        self._detection_future: concurrent.futures.Future | None = None
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="motion_detector_"
        )

        if self.stage >= 2:
            from app.overlay.motion.grid_mean_detector import GridMeanDetector
            from app.overlay.motion.grid_rms_detector import GridRMSDetector
            from app.overlay.motion.performance import PerformanceOptimizedDetector

            # Создаем базовый детектор в зависимости от algorithm
            if algorithm == "grid_rms":
                base_detector = GridRMSDetector(
                    grid_width=grid_width,
                    grid_height=grid_height,
                    threshold=threshold,
                    base_alpha=alpha,
                    alpha_fast_multiplier=alpha_fast_multiplier,
                    alpha_slow_multiplier=alpha_slow_multiplier,
                    use_adaptive_threshold=use_adaptive_threshold,
                    min_brightness=min_brightness,
                    max_change_threshold=max_change_threshold,
                )
            elif algorithm == "grid_mean":
                base_detector = GridMeanDetector(
                    grid_width=grid_width,
                    grid_height=grid_height,
                    threshold=threshold,
                    base_alpha=alpha,
                    alpha_fast_multiplier=alpha_fast_multiplier,
                    alpha_slow_multiplier=alpha_slow_multiplier,
                    use_adaptive_threshold=use_adaptive_threshold,
                    min_brightness=min_brightness,
                    max_change_threshold=max_change_threshold,
                )
            else:
                raise ValueError(f"Unknown algorithm: {algorithm}. Supported: 'grid_mean', 'grid_rms'")

            # Оборачиваем в оптимизатор производительности
            self.detector = PerformanceOptimizedDetector(
                detector=base_detector,
                max_detection_fps=max_detection_fps,
                skip_frames=skip_frames,
                enable_profiling=enable_profiling,
            )

    def render(self, frame: np.ndarray) -> None:
        """
        Отрисовать слой на кадре.

        Args:
            frame: Кадр в формате RGB
        """
        height, width = frame.shape[:2]
        cell_w, cell_h = calculate_cell_size(width, height, self.grid_width, self.grid_height)

        # STAGE 1: Только визуализация сетки
        if self.stage == 1:
            self._render_stage1(frame, cell_w, cell_h)

        # STAGE 2: Детекция движения + квадратики
        elif self.stage >= 2:
            self._render_stage2(frame, cell_w, cell_h)

    def _render_stage1(self, frame: np.ndarray, cell_w: int, cell_h: int) -> None:
        """
        Рендеринг Этапа 1: только сетка.

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        height, width = frame.shape[:2]

        # Рамка сетки
        cv2.rectangle(
            frame,
            (0, 0),
            (width - 1, height - 1),
            self.grid_line_color,
            self.grid_line_thickness,
            cv2.LINE_AA,
        )

        # Внутренние линии
        if self.show_grid_lines:
            self._draw_grid_lines(frame, cell_w, cell_h)

        # Номера ячеек (отладка)
        if self.show_cell_info:
            self._draw_cell_numbers(frame, cell_w, cell_h)

        # Статистика
        if self.show_stats:
            self._draw_stats_stage1(frame, cell_w, cell_h)

    def _render_stage2(self, frame: np.ndarray, cell_w: int, cell_h: int) -> None:
        """
        Рендеринг Этапа 2: детекция + квадратики.

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        # 1. Запустить детекцию в executor (освобождает GIL для OpenCV/NumPy)
        if self.detector is not None and (self._detection_future is None or self._detection_future.done()):
            try:
                loop = asyncio.get_running_loop()
                # Запускаем детекцию в executor (эквивалент asyncio.to_thread)
                self._detection_future = loop.run_in_executor(
                    self._executor,
                    self.detector.detect,
                    frame.copy()
                )
                # Добавляем callback для обновления motion_matrix
                self._detection_future.add_done_callback(self._on_detection_complete)
            except RuntimeError:
                # Нет running loop - пропускаем детекцию
                logger.debug("No running event loop, skipping motion detection")

        # 2. Отрисовать квадратики движения
        if self.motion_matrix is not None:
            self._draw_motion_boxes(frame, cell_w, cell_h)

        # 3. Опционально: линии сетки
        if self.show_grid_lines:
            self._draw_grid_lines(frame, cell_w, cell_h)

        # 4. Статистика
        if self.show_stats:
            self._draw_stats_stage2(frame, cell_w, cell_h)

    def _on_detection_complete(self, future: concurrent.futures.Future) -> None:
        """
        Callback для обновления результата детекции.

        Args:
            future: Future с результатом детекции
        """
        try:
            self.motion_matrix = future.result()
        except Exception as e:
            logger.error(f"Motion detection error: {e}", exc_info=True)

    def _draw_motion_boxes(self, frame: np.ndarray, cell_w: int, cell_h: int) -> None:
        """
        Отрисовка квадратиков с движением.

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        overlay = frame.copy()

        for j in range(self.grid_height):
            for i in range(self.grid_width):
                if self.motion_matrix[j, i] == 1:
                    x1, y1, x2, y2 = get_cell_bounds(i, j, cell_w, cell_h)

                    # Заливка (на overlay для прозрачности)
                    cv2.rectangle(
                        overlay,
                        (x1, y1),
                        (x2, y2),
                        self.box_color,
                        -1,  # Заливка
                    )

                    # Рамка (на основном кадре)
                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        self.box_color,
                        self.box_thickness,
                        cv2.LINE_AA,
                    )

        # Применяем прозрачность заливки
        if self.box_fill_alpha > 0:
            cv2.addWeighted(
                overlay,
                self.box_fill_alpha,
                frame,
                1 - self.box_fill_alpha,
                0,
                frame,
            )

    def _draw_grid_lines(self, frame: np.ndarray, cell_w: int, cell_h: int) -> None:
        """
        Отрисовка линий сетки.

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        height, width = frame.shape[:2]
        overlay = frame.copy()

        # Вертикальные линии
        for i in range(1, self.grid_width):
            x = i * cell_w
            cv2.line(
                overlay,
                (x, 0),
                (x, height),
                self.grid_line_color,
                self.grid_line_thickness,
                cv2.LINE_AA,
            )

        # Горизонтальные линии
        for j in range(1, self.grid_height):
            y = j * cell_h
            cv2.line(
                overlay,
                (0, y),
                (width, y),
                self.grid_line_color,
                self.grid_line_thickness,
                cv2.LINE_AA,
            )

        # Применяем прозрачность
        if self.grid_line_alpha < 1.0:
            cv2.addWeighted(
                overlay,
                self.grid_line_alpha,
                frame,
                1 - self.grid_line_alpha,
                0,
                frame,
            )

    def _draw_cell_numbers(
        self,
        frame: np.ndarray,
        cell_w: int,
        cell_h: int,
    ) -> None:
        """
        Нарисовать номера ячеек (для отладки).

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        font_scale = 0.3
        thickness = 1
        color = (255, 255, 255)  # Белый

        # Рисуем номера только в первых нескольких ячейках
        for j in range(min(3, self.grid_height)):
            for i in range(min(4, self.grid_width)):
                x = int(i * cell_w + 5)
                y = int(j * cell_h + 15)
                cv2.putText(
                    frame,
                    f"{i},{j}",
                    (x, y),
                    self.font,
                    font_scale,
                    color,
                    thickness,
                    cv2.LINE_AA,
                )

    def _draw_stats_stage1(
        self,
        frame: np.ndarray,
        cell_w: int,
        cell_h: int,
    ) -> None:
        """
        Отрисовать информацию о сетке (Этап 1).

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        height, width = frame.shape[:2]
        total_cells = self.grid_width * self.grid_height

        lines = [
            "Motion Detection - STAGE 1",
            f"Grid: {self.grid_width}x{self.grid_height} ({total_cells} cells)",
            f"Cell size: {cell_w}x{cell_h}px",
            f"Frame: {width}x{height}px",
        ]

        self._draw_info_box(frame, lines)

    def _draw_stats_stage2(
        self,
        frame: np.ndarray,
        cell_w: int,
        cell_h: int,
    ) -> None:
        """
        Отрисовать расширенную информацию о детекции (Этап 2).

        Args:
            frame: Кадр для отрисовки
            cell_w: Ширина ячейки в пикселях
            cell_h: Высота ячейки в пикселях
        """
        if self.motion_matrix is None:
            return

        motion_count = int(self.motion_matrix.sum())
        total_cells = self.grid_width * self.grid_height
        motion_percent = (motion_count / total_cells) * 100 if total_cells > 0 else 0

        # Название алгоритма
        algo_name = {"grid_mean": "Grid Mean", "grid_rms": "Grid RMS"}.get(
            self.algorithm, self.algorithm.title()
        )

        lines = [
            f"Motion Detection ({algo_name})",
            f"Motion: {motion_count}/{total_cells} ({motion_percent:.1f}%)",
            f"Grid: {self.grid_width}x{self.grid_height} (cell: {cell_w}x{cell_h}px)",
        ]

        # Добавляем статистику производительности
        if self.detector and self.show_performance:
            stats = self.detector.get_stats()
            if stats:
                # FPS информация
                if "actual_fps" in stats:
                    actual_fps = stats["actual_fps"]
                    target_fps = stats.get("target_fps", "∞")
                    lines.append(f"FPS: {actual_fps:.1f} (target: {target_fps})")

                # Время обработки
                if "avg_duration_ms" in stats:
                    avg_time = stats["avg_duration_ms"]
                    max_time = stats.get("max_duration_ms", 0)
                    lines.append(f"Time: {avg_time:.1f}ms (max: {max_time:.1f}ms)")

                # Статистика пропусков
                total_detections = stats.get("total_detections", 0)
                total_skipped = stats.get("total_skipped", 0)
                if total_skipped > 0:
                    skip_ratio = stats.get("skip_ratio", 0) * 100
                    lines.append(
                        f"Skipped: {total_skipped}/{total_detections + total_skipped} ({skip_ratio:.1f}%)"
                    )

        self._draw_info_box(frame, lines)

    def _draw_info_box(self, frame: np.ndarray, lines: list[str]) -> None:
        """
        Отрисовать информационный бокс.

        Args:
            frame: Кадр для отрисовки
            lines: Строки текста
        """
        # Параметры текста
        font_scale = 0.45
        thickness = 1
        line_height = 18
        padding = 10

        # Вычисляем размер фона с правильными отступами
        max_text_width = max(
            cv2.getTextSize(line, self.font, font_scale, thickness)[0][0] for line in lines
        )

        # Ширина и высота бокса (с учетом внутренних отступов)
        box_width = max_text_width + padding * 2
        box_height = len(lines) * line_height + padding * 2

        # Полупрозрачный фон
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (8, 8),
            (8 + box_width, 8 + box_height),
            (0, 0, 0),
            -1,
        )
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Рамка
        border_color = self.box_color if self.stage >= 2 else self.grid_line_color
        cv2.rectangle(
            frame,
            (8, 8),
            (8 + box_width, 8 + box_height),
            border_color,
            1,
        )

        # Текст
        for idx, line in enumerate(lines):
            y = 8 + padding + (idx + 1) * line_height - 5
            color = border_color if idx == 0 else (255, 255, 255)
            cv2.putText(
                frame,
                line,
                (8 + padding, y),
                self.font,
                font_scale,
                color,
                thickness,
                cv2.LINE_AA,
            )

    def __del__(self) -> None:
        """Cleanup executor при удалении layer."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
