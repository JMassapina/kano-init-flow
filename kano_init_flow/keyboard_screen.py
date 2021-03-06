# keyboard_screen.py
#
# Copyright (C) 2014-2015 Kano Computing Ltd.
# License: http://www.gnu.org/licenses/gpl-2.0.txt GNU General Public License v2
#

from gi.repository import Gtk, Gdk, GObject
import threading

from kano.network import is_internet
import kano_settings.system.keyboard_layouts as keyboard_layouts
import kano_settings.system.keyboard_config as keyboard_config
from kano_settings.config_file import get_setting, set_setting
from kano.gtk3.heading import Heading
from kano.gtk3.buttons import KanoButton
from kano.gtk3.kano_combobox import KanoComboBox
from kano.gtk3.kano_dialog import KanoDialog

from kano_init_flow.internet_screen import InternetScreen
from kano_init_flow.settings_intro_screen import SettingsIntroScreen

GObject.threads_init()

class KeyboardScreen(Gtk.Box):
    """
    Screen for selecting the keyboard layout
    """

    continents = [
        'Africa',
        'America',
        'Asia',
        'Australia',
        'Europe',
        'Others'
    ]

    def __init__(self, _win):
        self.selected_layout = None
        self.selected_country = None
        self.selected_variant = None

        self.selected_continent_index = 1
        self.selected_country_index = 21
        self.selected_variant_index = 0
        self.selected_continent_hr = "America"
        self.selected_country_hr = "USA"
        self.selected_variant_hr = "generic"

        # Set combobox styling to the screen
        KanoComboBox.apply_styling_to_screen()

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        self.win = _win
        self.win.set_main_widget(self)

        # Heading
        self.heading = Heading("Keyboard",
                               "Tell me where you live so I can set your keyboard.")
        self.heading.container.set_size_request(680, -1)

        heading_align = Gtk.Alignment()
        heading_align.add(self.heading.container)

        # Set padding around heading
        self.heading_align = Gtk.Alignment(yscale=0, yalign=0.5)

        # Button
        self.kano_button = KanoButton("APPLY CHANGES")
        self.kano_button.set_sensitive(False)  # Ensure continue button is enabled
        self.kano_button.connect("button_release_event", self.apply_changes)
        self.kano_button.connect("key_release_event", self.apply_changes)
        button_box = Gtk.ButtonBox(spacing=10)
        button_box.set_layout(Gtk.ButtonBoxStyle.SPREAD)
        button_box.add(self.kano_button)
        button_box.set_margin_bottom(30)

        # Create Continents Combo box
        self.continents_combo = KanoComboBox(max_display_items=7)
        self.continents_combo.connect("changed", self.on_continent_changed)
        for continent in self.continents:
            self.continents_combo.append(continent)

        # Create Countries Combo box
        self.countries_combo = self._create_combo_box(self.on_country_changed)

        # Create Advance mode checkbox
        self.advance_button = Gtk.CheckButton("Advanced options")
        self.advance_button.set_can_focus(False)
        self.advance_button.props.valign = Gtk.Align.CENTER
        self.advance_button.connect("clicked", self.on_advance_mode)
        self.advance_button.set_active(False)

        # Create Variants Combo box
        self.variants_combo = self._create_combo_box(self.on_variants_changed)

        self._set_dropdown_defaults()

        dropdown_container = self._create_dropdown_container()

        valign = Gtk.Alignment(xalign=0.5, yalign=0, xscale=0, yscale=0)
        valign.set_padding(15, 30, 0, 0)
        valign.add(dropdown_container)

        self.pack_start(heading_align, False, False, 0)
        self.pack_start(valign, False, False, 0)
        self.pack_start(button_box, False, False, 0)

        # Make the kano button grab the focus
        self.kano_button.grab_focus()

        # show all elements except the advanced mode
        self.refresh_window()

    @staticmethod
    def _create_combo_box(callback):
        """
        Generates a dropdown box which calls the provided
        callback whenever the selected item is changed

        :param callback: Callback for when the selected item is changed
        :returns: The generated combo box
        """

        combo = KanoComboBox(max_display_items=7)
        combo.connect("changed", callback)
        combo.props.valign = Gtk.Align.CENTER

        return combo

    def _create_countries_dropdown(self):
        """
        Generates a box which contain both the
        continent and country dropdown boxes

        :returns: The box
        """

        dropdown_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                               spacing=20)
        dropdown_box.set_size_request(230, 30)
        dropdown_box.props.valign = Gtk.Align.CENTER

        dropdown_box.pack_start(self.continents_combo, False,
                                False, 0)
        dropdown_box.pack_start(self.countries_combo, False,
                                False, 0)

        return dropdown_box

    def _create_keys_dropdown(self):
        """
        Generates a box which contain the variant
        dropdown box and the advanced button

        :returns: The box
        """

        dropdown_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                               spacing=20)
        dropdown_box.set_size_request(230, 30)

        dropdown_box.pack_start(self.advance_button, False, False, 0)
        dropdown_box.pack_start(self.variants_combo, False, False, 0)

        return dropdown_box

    def _create_dropdown_container(self):
        """
        Create various dropdown boxes so we can resize the dropdown
        lists appropriately. We create two boxes side by side, and
        then stack the country dropdow lists in one, and one by
        itself in the other

          dropdown_box_countries     dropdown_box_keys
        |                        |                        |
        |-------continents-------|   Advance option       |
        |                        |                        |
        |                        |                        |
        |-------countries -------|--------variants--------|
        |                        |                        |

        :returns: The box
        """

        dropdown_box_countries = self._create_countries_dropdown()
        dropdown_box_keys = self._create_keys_dropdown()


        dropdown_container = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                     spacing=20)
        dropdown_container.pack_start(dropdown_box_countries, False, False, 0)
        dropdown_container.pack_start(dropdown_box_keys, False, False, 0)

        return dropdown_container

    def _set_dropdown_defaults(self):
        """ Set up default values in dropdown lists """

        self.set_defaults("continent")
        self.fill_countries_combo(
            self.continents_combo.get_selected_item_text())

        self.set_defaults("country")
        self.on_country_changed(self.countries_combo)

        self.set_defaults("variant")

    def go_to_next_screen(self):
        """ Progress to the next screen in the flow """

        self.win.clear_win()

        if not is_internet():
            InternetScreen(self.win)
        else:
            SettingsIntroScreen(self.win)

    def refresh_window(self):
        """ Reset the window to default """

        self.win.show_all()
        self.variants_combo.hide()

    def apply_changes(self, _, event):
        """ Save changes """

        # If enter key is pressed or mouse button is clicked
        if not hasattr(event, 'keyval') or event.keyval == 65293:

            # Check for changes from default
            if not (self.selected_country.lower() == "us" and \
                    self.selected_variant == "generic"):

                # The settings will be applied in the background thread
                # while the loading cursor is being shown.
                self.set_busy()
                thread = threading.Thread(target=self.apply_keyboard_settings,
                                          args=(True,))
                thread.start()

            # keyboard does not need updating
            else:
                self.go_to_next_screen()

    def apply_keyboard_settings(self, confirm_dialog=False):
        """
            This function is meant to be run as a thread in the
            background.

            It will call self.keyboard_settings_applied_cb() within
            in the main GObject thread using idle_add when finished.
        """

        keyboard_config.set_keyboard(self.selected_country,
                                     self.selected_variant)

        GObject.idle_add(self.keyboard_settings_applied_cb, confirm_dialog)

    def keyboard_settings_applied_cb(self, confirm_dialog):
        self.set_busy(False)

        if not confirm_dialog or self.confirm_layout():
            self.update_config()
            self.go_to_next_screen()

        # This is to remove the callback from the main loop.
        return False

    def confirm_layout(self):
        """
            Shows the confirmation dialog asking the user to type some
            latin characters to make sure the layout of their choice does
            support it.

            :return: True if yes, False otherwise
            :rtype: bool
        """

        confirmation = KanoDialog(
            'Test your new keyboard layout',
            'Make sure you can write latin characters with your new ' \
            'layout, otherwise you won\'t be able to finish setting ' \
            'up your Kano. \n\n Type \'judoka\' into the box below ' \
            'or go back to the previous screen to choose a ' \
            'different layout:',
            [
                {
                    'label': 'OK',
                    'color': 'green',
                    'return_value': 1
                },
                {
                    'label': 'BACK',
                    'color': 'red',
                    'return_value': 0
                },
            ],
            widget=Gtk.Entry(),
            has_entry=True
        )
        rv = confirmation.run()
        del confirmation

        if rv != 0:
            if rv != 'judoka':
                try_again = KanoDialog(
                    "Try again",
                    "Please reconfigure your keyboard and try again."
                )
                try_again.run()
                del try_again
                return False
        else:
            # User clicked on back
            return False

        return True

    def set_busy(self, busy=True):
        """
            Sets/unsets this window's busy mode. This includes:

                * applying the loading cursor and
                * making the confirmation button insensitive.

            Not safe to be called from a thread.
        """

        if busy:
            watch_cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
            self.kano_button.start_spinner()
            self.win.get_window().set_cursor(watch_cursor)
            self.kano_button.set_sensitive(False)
        else:
            self.win.get_window().set_cursor(None)
            self.kano_button.stop_spinner()
            self.kano_button.set_sensitive(True)

    def update_config(self):
        """ Save the keyboard settings to the config file """

        # Add new configurations to config file.
        set_setting("Keyboard-continent-index", self.selected_continent_index)
        set_setting("Keyboard-country-index", self.selected_country_index)
        set_setting("Keyboard-variant-index", self.selected_variant_index)
        set_setting("Keyboard-continent-human", self.selected_continent_hr)
        set_setting("Keyboard-country-human", self.selected_country_hr)
        set_setting("Keyboard-variant-human", self.selected_variant_hr)

    def set_defaults(self, setting):
        """
        Set the default info on the dropdown lists
            "Keyboard-continent": [
                continents_combo,
                "Keyboard-country",
                "Keyboard-variant"
            ]:

        :params setting: can be "variant", "continent" or "country"
        """

        active_item = get_setting("Keyboard-" + setting + "-index")

        if setting == "continent":
            self.continents_combo.set_selected_item_index(int(active_item))
        elif setting == "country":
            self.countries_combo.set_selected_item_index(int(active_item))
        elif setting == "variant":
            self.variants_combo.set_selected_item_index(int(active_item))
        else:
            return

    def set_variants_to_generic(self):
        """ Set the layout variant to default """

        self.variants_combo.set_selected_item_index(0)

    def on_continent_changed(self, combo):
        """ Callback when a continent is selected """

        ## making sure the continent has been set
        continent_text = combo.get_selected_item_text()
        continent_index = combo.get_selected_item_index()
        if not continent_text or continent_index == -1:
            return

        self.selected_continent_hr = continent_text
        self.selected_continent_index = continent_index

        self.kano_button.set_sensitive(False)
        self.fill_countries_combo(self.selected_continent_hr)

        # Select the first by default
        self.countries_combo.set_selected_item_index(0)
        self.on_country_changed(self.countries_combo)

    def on_country_changed(self, combo):
        """ Callback when a country is selected """

        # making sure the country has been set
        country_text = combo.get_selected_item_text()
        country_index = combo.get_selected_item_index()
        if not country_text or country_index == -1:
            return

        # Remove entries from variants combo box
        self.variants_combo.remove_all()
        self.selected_country_hr = country_text
        self.selected_country_index = country_index

        # Refresh variants combo box
        self.selected_country = keyboard_config.find_country_code(
            country_text, self.selected_layout)
        variants = keyboard_config.find_keyboard_variants(self.selected_country)
        self.variants_combo.append("generic")
        if variants:
            for variant in variants:
                self.variants_combo.append(variant[0])

        self.set_variants_to_generic()
        self.on_variants_changed(self.variants_combo)

    def on_variants_changed(self, combo):
        """ Callback when a variant is selected """

        # making sure the variant has been set
        variant_text = combo.get_selected_item_text()
        variant_index = combo.get_selected_item_index()
        if not variant_text or variant_index == -1:
            return

        self.kano_button.set_sensitive(True)

        if variant_text == "generic":
            self.selected_variant = self.selected_variant_hr = variant_text
            self.selected_variant_index = 0
            return
        # Select the variant code
        variants = keyboard_config.find_keyboard_variants(self.selected_country)
        if variants is not None:
            for variant in variants:
                if variant[0] == variant_text:
                    self.selected_variant = variant[1]
                    self.selected_variant_index = variant_index
                    self.selected_variant_hr = variant_text

    def on_advance_mode(self, _):
        """ Callback when advanced mode is clicked """

        if int(self.advance_button.get_active()):
            self.variants_combo.show()
        else:
            self.variants_combo.hide()

    def work_finished_cb(self):
        """ Finished updating keyboard """
        pass

    def fill_countries_combo(self, continent):
        """ Populate the countries combo box """

        continent = continent.lower()

        try:
            self.selected_layout = keyboard_layouts.layouts[continent]
        except KeyError:
            return

        self.selected_continent_hr = continent

        # Remove entries from countries and variants combo box
        self.countries_combo.remove_all()
        self.variants_combo.remove_all()

        sorted_countries = sorted(self.selected_layout)

        # Refresh countries combo box
        for country in sorted_countries:
            self.countries_combo.append(country)
