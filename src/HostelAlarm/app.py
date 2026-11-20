"""
Hostel Alarm - monitors stars_count_0 from Zabbix API
"""

import json
import logging
import threading

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER

from .android_logger import setup_logging
from .zabbix import fetch_stars
from .alarm import AlarmManager

logger = logging.getLogger("HostelAlarm")

URL = "http://192.168.2.198:88/REST/zabbix/?key=ai-clear"


class HostelAlarm(toga.App):
    def startup(self):
        logger.info("App startup")
        self._watching = False
        self._threshold = 100
        self._poll_count = 0
        self._timer = None
        self._alarm_manager = AlarmManager()

        # --- Threshold display with +/- buttons ---
        self.threshold_label = toga.Label(
            "Threshold: 100",
            style=Pack(padding=(0, 0, 0, 10)),
        )
        minus_btn = toga.Button("-", on_press=self.on_minus, style=Pack(width=40))
        plus_btn = toga.Button("+", on_press=self.on_plus, style=Pack(width=40))
        threshold_box = toga.Box(
            children=[minus_btn, self.threshold_label, plus_btn],
            style=Pack(direction=ROW, alignment=CENTER),
        )

        # --- Watch button ---
        self.watch_button = toga.Button(
            "WATCH",
            on_press=self.on_watch,
            style=Pack(width=200, padding=(10, 0)),
        )

        # --- Stars count display ---
        self.stars_label = toga.Label(
            "Stars Count: --",
            style=Pack(font_size=20, padding=(20, 10), alignment=CENTER),
        )

        # --- Debug tick counter ---
        self.tick_label = toga.Label(
            "Ticks: 0",
            style=Pack(font_size=11, padding=(5, 10), alignment=CENTER),
        )

        # --- Status label ---
        self.status_label = toga.Label(
            "Ready",
            style=Pack(font_size=12, padding=(5, 10), alignment=CENTER),
        )

        # --- Main layout ---
        main_box = toga.Box(
            children=[
                threshold_box,
                self.watch_button,
                self.stars_label,
                self.tick_label,
                self.status_label,
            ],
            style=Pack(direction=COLUMN, alignment=CENTER, padding=20, flex=1),
        )

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()
        logger.info("UI ready")

    def on_minus(self, widget, **kwargs):
        if self._threshold > 1:
            self._threshold -= 1
            self.threshold_label.text = f"Threshold: {self._threshold}"
            logger.debug("Threshold decreased to %d", self._threshold)

    def on_plus(self, widget, **kwargs):
        if self._threshold < 500:
            self._threshold += 1
            self.threshold_label.text = f"Threshold: {self._threshold}"
            logger.debug("Threshold increased to %d", self._threshold)

    def on_watch(self, widget, **kwargs):
        if self._watching:
            self._stop_polling()
        else:
            self._start_polling()

    def _start_polling(self):
        logger.info("Starting polling")
        self._watching = True
        self._poll_count = 0
        self.watch_button.text = "WATCHING"
        self.status_label.text = "Polling every 5s..."
        self.poll_once()

    def _stop_polling(self):
        logger.info("Stopping polling")
        self._watching = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        self._alarm_manager.stop()
        self.watch_button.text = "WATCH"
        self.status_label.text = "Stopped"

    def poll_once(self):
        """Poll the API once, then schedule next poll."""
        self._poll_count += 1
        tick = self._poll_count
        logger.debug("poll_once tick=%d", tick)

        if not self._watching:
            logger.debug("poll_once: not watching, aborting")
            return

        try:
            stars = fetch_stars(URL)
            logger.debug("Fetched stars=%s", stars)
            if stars is not None:
                self.stars_label.text = f"Stars Count: {stars}"
                self._alarm_manager.check(stars, self._threshold)
                if self._alarm_manager.is_active():
                    self.status_label.text = f"ALARM — {stars} <= {self._threshold}"
                else:
                    self.status_label.text = f"OK — {stars} > {self._threshold}"
                self.tick_label.text = f"Ticks: {tick}"
                self.status_label.text = f"Polling every 5s... (tick {tick})"
            else:
                self.status_label.text = "Poll failed"
                logger.warning("fetch_stars returned None")
        except Exception as e:
            self.status_label.text = f"Error: {e}"
            logger.exception("poll_once failed")

        # Schedule next poll in 5 seconds
        logger.debug("Scheduling next poll in 5s")
        self._timer = threading.Timer(5, self.poll_once)
        self._timer.daemon = True
        self._timer.start()

    def _update_ui(self, stars, tick):
        """Update UI on main thread."""
        self.stars_label.text = f"Stars Count: {stars}"
        self._alarm_manager.check(stars, self._threshold)
        if self._alarm_manager.is_active():
            self.status_label.text = f"ALARM — {stars} <= {self._threshold}"
        else:
            self.status_label.text = f"OK — {stars} > {self._threshold}"
        self.tick_label.text = f"Ticks: {tick}"
        self.status_label.text = f"Polling every 30s... (tick {tick})"

    def _update_ui_error(self, error_msg, tick):
        """Update UI on main thread with error."""
        self.status_label.text = error_msg
        self.tick_label.text = f"Ticks: {tick}"
        self.status_label.text = f"{error_msg} (tick {tick})"


def main():
    setup_logging()
    return HostelAlarm()
