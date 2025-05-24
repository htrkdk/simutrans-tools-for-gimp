#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This program is a reimplementation/modification of a script originally
# licensed under the Simutrans Artistic License.
#
# Original Author: Fabio
# Original Work: SIMUTRANS TOOLS FOR GIMP
# License: Simutrans Artistic License
# See: https://forum.simutrans.com or https://www.simutrans.com
#
# This version retains the original license, and is distributed under the
# same terms:
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the Simutrans Artistic License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import sys

import gi
gi.require_version('Gimp', '3.0')
gi.require_version('GimpUi', '3.0')
from gi.repository import Gimp, GimpUi, GObject, Gegl, GLib, Gio


# GIMP specific functions

def N_(message):
    return message


def _(message):
    return GLib.dgettext(None, message)


def all_layers_in_image(l_root_layers: list):
    l_all_layers = []

    for layer in l_root_layers:
        if layer.is_group() is True:
            l_children = layer.get_children()
            l_all_layers.extend(all_layers_in_image(l_children))
        else:
            l_all_layers.append(layer)

    return l_all_layers


# CONSTANTS AND LISTS

l_non_darkening_greys = [
    "#6B6B6B", "#9B9B9B", "#B3B3B3", "#C9C9C9", "#DFDFDF"
]

l_window_colors = [
    "#4D4D4D", "#57656F", "#C1B1D1", "#E3E3FF"
]

l_primary_player_colors = [
    "#244B67", "#395E7C", "#4C7191", "#6084A7", "#7497BD", "#88ABD3",
    "#9CBEE9", "#B0D2FF"
]

l_secondary_player_colors = [
    "#7B5803", "#8E6F04", "#A18605", "#B49D07", "#C6B408", "#D9CB0A",
    "#ECE20B", "#FFF90D"
]

l_lights = [
    "#7F9BF1", "#FFFF53", "#FF211D", "#01DD01", "#FF017F", "#0101FF"
]

l_transparent_color = [
    "#E7FFFF"
]


class SimutransSpecialColorsHelper(Gimp.PlugIn):
    """
    Simutrans Special Colors Helper

    Difference from the original script:
    - allows multiple layer operation
    - "Only in current selection" option now available for all operations

    Supported operations:
        select, remove, repair, lighten / darken, lookup (convert)
    """

    def do_query_procedures(self):
        return ["plug-in-htrkdk-simutrans-special-colors-helper"]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(
            self, name, Gimp.PDBProcType.PLUGIN, self.run, None)

        procedure.set_image_types("*")

        procedure.set_menu_label("Special Colors Helper...")
        procedure.add_menu_path('<Image>/Simutrans/Color Tools')

        procedure.set_documentation(
            "Select, remove or repair Simutrans special colors",
            name
        )
        procedure.set_attribution("htrkdk", "htrkdk", "2025")

        op_choices = Gimp.Choice.new()
        op_choices.add("op_select", 0,
                       "Select special colors",
                       "Select special colors")
        op_choices.add("op_remove", 1,
                       "Remove special colors",
                       "Remove special colors")
        op_choices.add("op_repair", 2,
                       "Repair special colors",
                       "Repair special colors")
        op_choices.add("op_lighten", 3,
                       "Lighten special colors",
                       "Lighten special colors")
        op_choices.add("op_darken", 4,
                       "Darken special colors",
                       "Darken special colors")
        op_choices.add("op_lookup", 5,
                       "Convert to special colors",
                       "Convert to special colors")
        procedure.add_choice_argument(
            "operation", _("O_peration to perform"),
            "Operation to perform",
            op_choices,
            "op_select",
            GObject.ParamFlags.READWRITE
        )
        procedure.add_boolean_argument(
            "non_darkening_greys", _("_Non-darkening greys"),
            "Non-darkening greys",
            True,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_boolean_argument(
            "window_colors", ("_Windows"),
            "Windows",
            True,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_boolean_argument(
            "primary_player_colors", _("Player colors (Pr_imary)"),
            "Player colors (Primary)",
            True,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_boolean_argument(
            "secondary_player_colors", _("Player colors (S_econdary)"),
            "Player colors (Secondary)",
            True,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_boolean_argument(
            "lights", _("Li_ghts (except lighten/darken)"),
            "Lights (except lighten/darken)",
            False,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_boolean_argument(
            "transparent_color", _("_Transparent (except lighten/darken)"),
            "Transparent (except lighten/darken)",
            False,
            GObject.ParamFlags.READWRITE
        )
        layer_choices = Gimp.Choice.new()
        layer_choices.add("layer_selected", 0,
                          "Selected flat layers",
                          "help")
        layer_choices.add("layer_all", 1,
                          "All flat layers",
                          "help")
        layer_choices.add("layer_merged", 2,
                          "Sample merged (only select)",
                          "help")
        procedure.add_choice_argument(
            "layers_option", _("_Apply to"),
            "Apply to",
            layer_choices,
            "layer_selected",
            GObject.ParamFlags.READWRITE
        )
        sel_choices = Gimp.Choice.new()
        sel_choices.add("sel_replace", 0,
                        "Replace current selection",
                        "Replace current selection")
        sel_choices.add("sel_current", 1,
                        "Only in current selection",
                        "Only in current selection")
        sel_choices.add("sel_add", 2,
                        "Add to current selection (only select)",
                        "Add to current selection (only select)")
        sel_choices.add("sel_subtract", 3,
                        "Subtract from current selection (only select)",
                        "Subtract from current selection (only select)")
        procedure.add_choice_argument(
            "select_mode", _("Selection _mode"),
            "Selection mode",
            sel_choices,
            "sel_replace",
            GObject.ParamFlags.READWRITE
        )
        procedure.add_double_argument(
            "threshold", _("T_hreshold (only repair)"),
            "Threshold (only repair)",
            0, 255, 15,
            GObject.ParamFlags.READWRITE
        )
        procedure.add_file_argument(
            "lookup_file", _("Look_up image (only convert)"),
            "Look_up image (only convert)",
            Gimp.FileChooserAction.OPEN,
            False,
            None,
            GObject.ParamFlags.READWRITE
        )

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("plug-in-htrkdk-simutrans-special-colors-helper")
            dialog = GimpUi.ProcedureDialog.new(procedure, config)
            dialog.fill(None)

        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL,
                                               GLib.Error())
        else:
            dialog.destroy()

        operation = config.get_property("operation")
        non_darkening_greys = config.get_property("non_darkening_greys")
        window_colors = config.get_property("window_colors")
        primary_player_colors = config.get_property("primary_player_colors")
        secondary_player_colors = config.get_property("secondary_player_colors")
        lights = config.get_property("lights")
        transparent_color = config.get_property("transparent_color")
        layers_option = config.get_property("layers_option")
        select_mode = config.get_property("select_mode")
        threshold = config.get_property("threshold")
        lookup_file = config.get_property("lookup_file")

        image.undo_group_start()
        Gimp.context_push()

        # modify exactly the same color with the target
        Gimp.context_set_antialias(False)
        Gimp.context_set_sample_threshold(0.0)

        # Variables
        selection = \
            None if Gimp.Selection.is_empty(image) \
            else Gimp.Selection.save(image)
        l_color_set = []

        # Add selected special color sets to the list
        if non_darkening_greys:
            l_color_set.extend(l_non_darkening_greys)
        if window_colors:
            l_color_set.extend(l_window_colors)
        if primary_player_colors:
            l_color_set.extend(l_primary_player_colors)
        if secondary_player_colors:
            l_color_set.extend(l_secondary_player_colors)

        if operation == "op_darken":
            pass
        elif operation == "op_lighten":
            l_color_set.reverse()
        else:
            if lights:
                l_color_set.extend(l_lights)
            if transparent_color:
                l_color_set.extend(l_transparent_color)

        # Special initialization
        if layers_option == "layer_all":
            l_layers = all_layers_in_image(image.get_layers())
        else:
            l_layers = drawables

        if layers_option == "layer_merged":
            # If sample merged, force Select operation
            operation = "op_select"
            Gimp.context_set_sample_merged(True)
        else:
            Gimp.context_set_sample_merged(False)

        if operation == "op_select":
            if select_mode != "sel_add":
                Gimp.Selection.none(image)
        elif operation == "op_repair":
            Gimp.context_set_sample_threshold(threshold/255.0)
        elif operation == "op_lookup":
            if lookup_file is None:
                Gimp.message(
                    "Lookup image must not be None for convert operation.")
                return procedure.new_return_values(
                    Gimp.PDBStatusType.EXECUTION_ERROR, GLib.Error())

            # If Lookup operation, open lookup image and sets orientation
            lookup_image = Gimp.file_load(
                Gimp.RunMode.NONINTERACTIVE,
                lookup_file
            )
            lookup_image_layer = lookup_image.get_layers()[0]
            lu_height = lookup_image.get_height()
            lu_width = lookup_image.get_width()
            lookup_vertical = True if (lu_height > lu_width) else False

        for target_layer in l_layers:
            for target_color_code in l_color_set:
                target_color = Gegl.Color.new(target_color_code)

                if operation == "op_select":
                    image.select_color(
                        Gimp.ChannelOps.ADD,
                        target_layer,
                        target_color
                    )
                elif operation == "op_lookup":
                    lookup_image.select_color(
                        Gimp.ChannelOps.REPLACE,
                        lookup_image_layer,
                        target_color
                    )
                    koord = Gimp.Selection.bounds(lookup_image)
                    Gimp.Selection.none(lookup_image)

                    # if lookup color is not empty, register (x,y) coordinates
                    if koord[1]:
                        x1 = koord[2]
                        y1 = koord[3]
                        x2 = koord[4] - 1
                        y2 = koord[5] - 1
                    else:
                        continue

                    while True:
                        x1 += 1 if lookup_vertical else 0
                        y1 += 0 if lookup_vertical else 1
                        x2 += 1 if lookup_vertical else 0
                        y2 += 0 if lookup_vertical else 1

                        color1 = lookup_image.pick_color(
                            [lookup_image_layer], x1, y1, False, False, 0)
                        color2 = lookup_image.pick_color(
                            [lookup_image_layer], x2, y2, False, False, 0)

                        if color1[0] and color2[0] and \
                           (color1[1].get_rgba() == color2[1].get_rgba()):
                            lu_color = color1[1]
                            break
                        elif y2 >= lu_height or x2 >= lu_width:
                            lu_color = None
                            break

                    if lu_color is None:
                        continue

                    image.select_color(
                        Gimp.ChannelOps.REPLACE,
                        target_layer,
                        lu_color
                    )
                    if select_mode == "sel_current" and selection is not None:
                        image.select_item(
                            Gimp.ChannelOps.INTERSECT,
                            selection,
                        )
                    if not Gimp.Selection.is_empty(image):
                        Gimp.context_set_foreground(target_color)
                        target_layer.edit_fill(Gimp.FillType.FOREGROUND)
                else:
                    image.select_color(
                        Gimp.ChannelOps.REPLACE,
                        target_layer,
                        target_color
                    )

                    if Gimp.Selection.is_empty(image):
                        continue
                    elif select_mode == "sel_current" and selection is not None:
                        image.select_item(
                            Gimp.ChannelOps.INTERSECT,
                            selection,
                        )

                    if operation == "op_remove":
                        prev_color_rgba = target_color.get_rgba()
                        repaired_color_rgb = [x - 1/255 if x > 0 else x + 1/255
                                              for x in prev_color_rgba[:-1]]
                        target_color.set_rgba(repaired_color_rgb[0],
                                              repaired_color_rgb[1],
                                              repaired_color_rgb[2],
                                              prev_color_rgba[3])
                        Gimp.context_set_foreground(target_color)
                        target_layer.edit_fill(Gimp.FillType.FOREGROUND)
                    elif operation == "op_repair":
                        Gimp.context_set_foreground(target_color)
                        target_layer.edit_fill(Gimp.FillType.FOREGROUND)
                    elif operation == "op_darken" or operation == "op_lighten":
                        prev_color_i = l_color_set.index(target_color_code) - 1
                        if prev_color_i < 0:
                            continue

                        prev_color = Gegl.Color.new(l_color_set[prev_color_i])
                        Gimp.context_set_foreground(prev_color)
                        target_layer.edit_fill(Gimp.FillType.FOREGROUND)

        # Special termination for some operations
        if operation == "op_lookup":
            # If Lookup operation, close lookup image
            lookup_image.delete()

        # Reset or mask operation
        if selection is None:
            # No initial selection
            if operation != "op_select":
                Gimp.Selection.none(image)
        else:
            # Existing selection
            if operation == "op_select":
                if select_mode == "sel_current":
                    image.select_item(
                        Gimp.ChannelOps.INTERSECT,
                        selection
                    )
                elif select_mode == "sel_subtract":
                    image.select_item(
                        Gimp.ChannelOps.SUBTRACT,
                        selection
                    )
            else:
                image.select_item(
                    Gimp.ChannelOps.ADD,
                    selection
                )

        Gimp.message("Operation done successfully for %d layers."
                     % (len(l_layers)))

        Gimp.context_pop()
        image.undo_group_end()
        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS,
                                           GLib.Error())


Gimp.main(SimutransSpecialColorsHelper.__gtype__, sys.argv)
