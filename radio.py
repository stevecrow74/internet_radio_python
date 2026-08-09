#!/usr/bin/env python3

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gst, GLib

Gst.init(None)

STATIONS = [
    ("Radio X", "https://icecast.thisisdax.com/RadioXUK"),
    ("Zenith Rock", "http://91.189.64.188:3644/zenith128mp3"),
    ("Classic Hits", "http://live-bauerie.sharp-stream.com/CLASSIC?ref=RF"),
    ("Classic FM", "http://media-ice.musicradio.com/ClassicFMMP3"),
    ("BoB FM", "http://sirius.shoutca.st:8011/stream"),
    ("Onic Alt", "http://onic.dublin.live.stream.broadcasting.news/stream-alternative-mobile?ref=RF"),
    ("Velvet", "http://stream.btsstream.com:8012/velvet.mp3"),
    ("Onic 80's", "http://onic.dublin.live.stream.broadcasting.news/stream-80s?ref=RF"),
    ("Darkwave Radio", "http://77.249.39.15:8000/;"),
    ("Soma 80's", "https://ice6.somafm.com/u80s-64-aac"),
    ("Soma Indie", "https://ice6.somafm.com/indiepop-128-mp3"),
    ("Soma Doomed", "https://ice5.somafm.com/doomed-128-mp3"),
    ("Soma 70's", "https://ice5.somafm.com/seventies-128-mp3"),
    ("Mellow Mix", "https://stream.radioparadise.com/mellow-320"),
    ("Rock Mix", "https://stream.radioparadise.com/rock-320"),
    ("Rock Antenne Classic", "https://stream.rockantenne.de/classic-perlen"),
    ("Rock Antenne Alternative", "https://stream.rockantenne.de/alternative"),
    ("Rock Antenne Heavy Metal", "https://stream.rockantenne.de/heavy-metal"),
]

PAGE_SIZE = 6


class Radio(Gtk.Window):
    def __init__(self):
        super().__init__(title="Internet Radio")

        self.set_default_size(480, 320)
        self.set_resizable(True)
        self.set_decorated(False)

        self.page = 0
        self.current = None
        self.current_station = None

        self.player = Gst.ElementFactory.make("playbin", "player")

        # Listen for stream metadata
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_gst_message)

        self.connect("destroy", self.quit)

        css = Gtk.CssProvider()
        css.load_from_data(b"""
        window {
            background: #101010;
        }

        button {
            background: #303030;
            color: white;
            border-radius: 8px;
            border: 2px solid #505050;
            font-size: 17px;
            font-weight: bold;
            padding: 5px;
        }

        button:hover {
            background: #505050;
        }

        button:active {
            background: #707070;
        }

        label {
            color: white;
        }

        .now-playing {
            background: #202020;
            color: #ffffff;
            border: 2px solid #505050;
            border-radius: 8px;
            padding: 5px;
            font-size: 15px;
            font-weight: bold;
        }
        """)

        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.build_ui()

    def build_ui(self):
        main = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4
        )

        main.set_margin_top(4)
        main.set_margin_bottom(4)
        main.set_margin_start(5)
        main.set_margin_end(5)

        self.title = Gtk.Label()
        self.title.set_markup(
            "<span size='large' weight='bold'>INTERNET RADIO</span>"
        )
        main.pack_start(self.title, False, False, 0)

        self.now = Gtk.Label(label="Select a station")
        self.now.set_ellipsize(3)
        main.pack_start(self.now, False, False, 0)

        grid = Gtk.Grid()
        grid.set_row_spacing(4)
        grid.set_column_spacing(4)

        start = self.page * PAGE_SIZE
        stations = STATIONS[start:start + PAGE_SIZE]

        for n, (name, url) in enumerate(stations):
            button = Gtk.Button(label=name)
            button.set_hexpand(True)
            button.set_vexpand(True)
            button.connect(
                "clicked",
                self.station_clicked,
                start + n
            )

            grid.attach(
                button,
                n % 2,
                n // 2,
                1,
                1
            )

        main.pack_start(grid, True, True, 0)

        # Main controls
        controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=5
        )

        prev = Gtk.Button(label="◀")
        prev.connect("clicked", self.previous_page)

        stop = Gtk.Button(label="■")
        stop.connect("clicked", self.stop)

        next_button = Gtk.Button(label="▶")
        next_button.connect("clicked", self.next_page)

        vol_down = Gtk.Button(label="VOL −")
        vol_down.connect("clicked", self.volume_down)

        vol_up = Gtk.Button(label="VOL +")
        vol_up.connect("clicked", self.volume_up)

        for button in (
            prev,
            stop,
            next_button,
            vol_down,
            vol_up
        ):
            button.set_hexpand(True)
            controls.pack_start(button, True, True, 0)

        main.pack_start(controls, False, False, 0)

        # ------------------------------------------
        # NOW PLAYING BAR
        # ------------------------------------------
        self.now_playing = Gtk.Label(
            label="Now playing — Select a station"
        )

        self.now_playing.set_ellipsize(3)
        self.now_playing.set_xalign(0.5)
        self.now_playing.set_hexpand(True)
        self.now_playing.set_size_request(-1, 34)

        self.now_playing.get_style_context().add_class(
            "now-playing"
        )

        main.pack_start(
            self.now_playing,
            False,
            False,
            0
        )

        self.add(main)
        self.show_all()

    def station_clicked(self, button, index):
        name, url = STATIONS[index]

        self.player.set_state(Gst.State.NULL)

        self.current = index
        self.current_station = name

        # Reset metadata display
        self.now_playing.set_text(
            "Now playing — " + name
        )

        self.player.set_property("uri", url)
        self.player.set_state(Gst.State.PLAYING)

        self.now.set_markup(
            "<span size='large' weight='bold'>" +
            GLib.markup_escape_text(name) +
            "</span>"
        )

    def on_gst_message(self, bus, message):
        """
        Read ICY/stream metadata from GStreamer.
        """

        if message.type != Gst.MessageType.TAG:
            return

        taglist = message.parse_tag()

        artist = None
        title = None

        # Try standard GStreamer tags
        success, value = taglist.get_string("artist")
        if success:
            artist = value.strip()

        success, value = taglist.get_string("title")
        if success:
            title = value.strip()

        # Some internet radio streams provide only a title.
        if title:
            if artist:
                text = f"{artist} — {title}"
            else:
                text = title

            self.now_playing.set_text(text)

    def stop(self, button):
        self.player.set_state(Gst.State.NULL)

        self.now.set_text("Stopped")
        self.now_playing.set_text("Stopped")

    def volume_down(self, button):
        volume = self.player.get_property("volume")
        self.player.set_property(
            "volume",
            max(0.0, volume - 0.1)
        )

    def volume_up(self, button):
        volume = self.player.get_property("volume")
        self.player.set_property(
            "volume",
            min(1.0, volume + 0.1)
        )

    def previous_page(self, button):
        self.page -= 1

        if self.page < 0:
            self.page = (len(STATIONS) - 1) // PAGE_SIZE

        self.rebuild()

    def next_page(self, button):
        self.page += 1

        if self.page > (len(STATIONS) - 1) // PAGE_SIZE:
            self.page = 0

        self.rebuild()

    def rebuild(self):
        for child in self.get_children():
            self.remove(child)

        self.build_ui()

    def quit(self, widget):
        self.player.set_state(Gst.State.NULL)
        Gtk.main_quit()


Radio()
Gtk.main()
