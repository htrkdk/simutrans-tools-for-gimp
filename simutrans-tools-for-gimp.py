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
import os

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


class SimutransTool(Gimp.PlugIn):
    def do_query_procedures(self):
        return ["plug-in-htrkdk-simutrans-special-colors-helper",
                "plug-in-htrkdk-simutrans-export",
                "plug-in-htrkdk-simutrans-set-grid"]

    def do_set_i18n(self, name):
        return False

    def do_create_procedure(self, name):
        if name == "plug-in-htrkdk-simutrans-special-colors-helper":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_color_helper, None)

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

        elif name == "plug-in-htrkdk-simutrans-export":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_exporter, None)

            procedure.set_image_types("*")

            procedure.set_menu_label("Export with transparent background...")
            procedure.add_menu_path('<Image>/Simutrans/Image Tools')

            procedure.set_documentation(
                "Export to PNG adding a transparent special color background",
                name
            )
            procedure.set_attribution("htrkdk", "htrkdk", "2026")

            procedure.add_string_argument(
                "suffix", _("_Custom suffix (e.g. -01)"),
                "Custom suffix (e.g. -01)",
                "",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "flatten_alpha", _("_Flatten Alpha Channel"),
                "Flatten Alpha Channel",
                True,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_double_argument(
                "alpha_threshold", _("Alpha _Threshold"),
                "Alpha Threshold",
                0,      # min
                1,      # max
                0.5,    # default
                GObject.ParamFlags.READWRITE
            )

            return procedure

        elif name == "plug-in-htrkdk-simutrans-set-grid":
            procedure = Gimp.ImageProcedure.new(
                self, name, Gimp.PDBProcType.PLUGIN, self.run_grid, None)

            procedure.set_image_types("*")

            procedure.set_menu_label("Set tiles grid...")
            procedure.add_menu_path('<Image>/Simutrans/Image Tools')

            procedure.set_documentation(
                "Set grid for chosen tileset size",
                name
            )
            procedure.set_attribution("htrkdk", "htrkdk", "2026")

            size_choices = Gimp.Choice.new()
            size_choices.add("32", 0, "32", "32")
            size_choices.add("48", 1, "48", "48")
            size_choices.add("64", 2, "64", "64")
            size_choices.add("96", 3, "96", "96")
            size_choices.add("128", 4, "128", "128")
            size_choices.add("160", 5, "160", "160")
            size_choices.add("192", 6, "192", "192")
            size_choices.add("256", 7, "256", "256")
            procedure.add_choice_argument(
                "tile_size", _("Tile _Size"),
                "Tile Size",
                size_choices,
                "128",
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "resize_image", _("Resize _Image"),
                "Resize Image",
                False,
                GObject.ParamFlags.READWRITE
            )
            procedure.add_boolean_argument(
                "resize_layer", _("Resize _Layer"),
                "Resize Layer",
                False,
                GObject.ParamFlags.READWRITE
            )

            return procedure


    def run_color_helper(self, procedure, run_mode, image, drawables, config, run_data):
        """
        Simutrans Special Colors Helper

        Difference from the original script:
        - allows multiple layer operation
        - "Only in current selection" option now available for all operations

        Supported operations:
            select, remove, repair, lighten / darken, lookup (convert)
        """

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

    def run_exporter(self, procedure, run_mode, image, drawables, config, run_data):
        """
        Simutrans Export

        Difference from the original script:
        - Allows fully transparent pixels since Simutrans officially supports them.
        - Ignore threshold alpha value if flatten image is disabled.
        """

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("plug-in-htrkdk-simutrans-export")
            dialog = GimpUi.ProcedureDialog.new(procedure, config)
            dialog.fill(None)

        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL,
                                               GLib.Error())
        else:
            dialog.destroy()

        suffix = config.get_property("suffix")
        flatten_alpha = config.get_property("flatten_alpha")
        alpha_threshold = config.get_property("alpha_threshold")
        background_color = Gegl.Color.new(l_transparent_color[0])

        # modify filename
        orig_file = image.get_file()

        if not orig_file:
            # TODO: call a dialog to fill in proper filename or save image as xcf
            Gimp.message("Please save your image as a xcf file before exportation.")

            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL,
                                               GLib.Error())

        orig_name = orig_file.get_path()
        base_name, orig_ext = os.path.splitext(orig_name)

        if orig_ext == ".gz" or orig_ext == ".bz2":
            base_name, orig_ext = os.path.splitext(base_name)

        export_name = base_name + suffix + ".png"

        Gimp.context_push()
        Gimp.context_set_background(background_color)
        export_image = image.duplicate()
        export_image.undo_group_start()

        visible = export_image.pick_correlate_layer(0, 0)

        if flatten_alpha:
            # set alpha threshold
            export_layer = export_image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)
            filter_threshold_alpha = Gimp.DrawableFilter.new(
                export_layer,
                "gimp:threshold-alpha",
                None
            )
            filter_threshold_alpha.set_opacity(alpha_threshold)
            export_layer.merge_filter(filter_threshold_alpha)

            # insert background layer if transparent
            if visible == -1:
                bg_layer = Gimp.Layer.new(
                    export_image,
                    "bg_tmp",
                    export_image.get_width(),
                    export_image.get_height(),
                    Gimp.ImageType.RGB_IMAGE,
                    1.0,
                    Gimp.LayerMode.NORMAL
                )
                export_image.insert_layer(bg_layer, 0, 0)
                export_layer = export_image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)

            # replace background color with default of Simutrans
            pick_status, prev_bg = \
                export_image.pick_color([export_layer], 1, 1, False, False, 0)

            if pick_status:
                export_image.select_color(
                    Gimp.ChannelOps.REPLACE,
                    export_layer,
                    prev_bg
                )
                if not Gimp.Selection.is_empty(export_image):
                    export_layer.edit_fill(Gimp.FillType.BACKGROUND)

                Gimp.Selection.none(export_image)

            # flatten alpha
            export_layer = export_image.flatten()

        else:
            export_layer = export_image.merge_visible_layers(Gimp.MergeType.CLIP_TO_IMAGE)

            # if background is not transparent, fix it to default of Simutrans
            if visible != -1:
                pick_status, prev_bg = \
                    export_image.pick_color([export_layer], 1, 1, False, False, 0)

                if pick_status:
                    export_image.select_color(
                        Gimp.ChannelOps.REPLACE,
                        export_layer,
                        prev_bg
                    )
                    if not Gimp.Selection.is_empty(export_image):
                        export_layer.edit_fill(Gimp.FillType.BACKGROUND)

                    Gimp.Selection.none(export_image)

        # save modified image
        Gimp.file_save(
            Gimp.RunMode.NONINTERACTIVE,
            export_image,
            Gio.File.new_for_path(export_name),
            None
        )

        Gimp.message("Exported png file "+str(export_name))

        Gimp.context_pop()
        export_image.undo_group_end()
        export_image.delete()
        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS,
                                           GLib.Error())

    def run_grid(self, procedure, run_mode, image, drawables, config, run_data):
        """
        Simutrans Set Grid
        """

        if run_mode == Gimp.RunMode.INTERACTIVE:
            GimpUi.init("plug-in-htrkdk-simutrans-set-grid")
            dialog = GimpUi.ProcedureDialog.new(procedure, config)
            dialog.fill(None)

        if not dialog.run():
            dialog.destroy()
            return procedure.new_return_values(Gimp.PDBStatusType.CANCEL,
                                               GLib.Error())
        else:
            dialog.destroy()

        spacing = int(config.get_property("tile_size"))
        resize_image = config.get_property("resize_image")
        resize_layer = config.get_property("resize_layer")

        # get size of original image
        height = image.get_height()
        width = image.get_width()

        image.undo_group_start()
        Gimp.context_push()

        if resize_image:
            if height % spacing == 0:
                new_height = height
            else:
                new_height = (height // spacing + 1) * spacing

            if width % spacing == 0:
                new_width = width
            else:
                new_width = (width // spacing + 1) * spacing

            if height != new_height or width != new_width:
                image.resize(new_width, new_height, 0, 0)

            if resize_layer:
                for layer in all_layers_in_image(image.get_layers()):
                    if layer.get_height() == height and layer.get_width() == width:
                        layer.resize_to_image_size()

        image.grid_set_spacing(spacing, spacing)
        image.grid_set_offset(0, 0)

        Gimp.message("Changed tile size of the image to "+str(spacing))

        Gimp.context_pop()
        image.undo_group_end()
        Gimp.displays_flush()

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS,
                                           GLib.Error())


Gimp.main(SimutransTool.__gtype__, sys.argv)
