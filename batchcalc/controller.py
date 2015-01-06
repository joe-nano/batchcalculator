# controller.py
#
# -*- coding: utf-8 -*-
#
#    Zeolite Batch Calculator
#
# A program for calculating the correct amount of reagents (batch) for a
# particular zeolite composition given by the molar ratio of its components.
#
# The MIT License (MIT)
#
# Copyright (c) 2014 Lukasz Mentel
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__version__ = "0.2.0"

import wx

from batchcalc.calculator import Chemical, Component, Electrolyte, Kind, Category, Reaction, PhysicalForm, Batch
from batchcalc import dialogs


class AddModifyBatchRecordDialog(wx.Dialog):

    def __init__(self, parent, session=None, record=None, title="Add", add_record=True,
            pos=wx.DefaultPosition, size=(800, 230)):

        super(AddModifyBatchRecordDialog, self).__init__(parent, id=wx.ID_ANY, title="{0:s} a Batch Record".format(title), size=size)

        self.panel = wx.Panel(self)

        # attributes
        self.session = session
        self.record = record
        self.add_record = add_record
        if record is not None:
            v_coeff = "{0:6.2f}".format(record.coefficient)
        else:
            v_coeff = ""

        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)

        lbl_title = wx.StaticText(self.panel, -1, "{0:s} Batch Record".format(title))
        lbl_title.SetFont(font)
        lbl_chemical = wx.StaticText(self.panel, -1, "Chemical")
        lbl_component = wx.StaticText(self.panel, -1, "Component")
        lbl_coeff = wx.StaticText(self.panel, -1, "Coefficient")
        lbl_reaction = wx.StaticText(self.panel, -1, "Reaction")

        self.txtc_coeff = wx.TextCtrl(self.panel, -1, v_coeff)

        chemicals = parent.model.get_chemicals(showall=True)
        components = parent.model.get_components()
        reactions = parent.model.get_reactions()

        self.chemicals  = {i:c for i,c in zip(range(len(chemicals)), chemicals)}
        self.components = {i:c for i,c in zip(range(len(components)), components)}
        self.reactions  = {i:c for i,c in zip(range(len(reactions)), reactions)}

        self.ch_chemical  = wx.Choice(self.panel, -1, (50, 20), choices=[x.name for x in chemicals])
        self.ch_component = wx.Choice(self.panel, -1, (50, 20), choices=[x.name for x in components])
        self.ch_reaction  = wx.Choice(self.panel, -1, (50, 20), choices=[x.reaction for x in reactions])

        if record is not None:
            if self.record.chemical is not None:
                self.ch_chemical.SetStringSelection(self.record.chemical)
            if self.record.component is not None:
                self.ch_component.SetStringSelection(self.record.component)
            if self.record.reaction is not None:
                self.ch_reaction.SetStringSelection(self.record.reaction)

        sizer = wx.GridBagSizer(vgap=5, hgap=5)
        sizer.Add(lbl_title,     pos=(0, 0), span=(1, 3), flag=wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, border=10)
        sizer.Add(lbl_chemical,  pos=(1, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_component, pos=(1, 1), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_coeff,     pos=(1, 2), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_reaction,  pos=(3, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)

        sizer.Add(self.ch_chemical,  pos=(2, 0), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.ch_component, pos=(2, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_coeff,   pos=(2, 2), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.ch_reaction,  pos=(4, 0), span=(1, 2), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)

        buttonOk = wx.Button(self.panel, id=wx.ID_ANY, label="{0:s}".format(title))
        buttonOk.SetDefault()
        buttonOk.Bind(wx.EVT_BUTTON, self.OnSaveRecord)
        buttonCancel = wx.Button(self.panel, id=wx.ID_CANCEL)
        buttonCancel.Bind(wx.EVT_BUTTON, self.OnClose)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(buttonOk, flag=wx.RIGHT|wx.LEFT, border=5)
        hbox.Add(buttonCancel, flag=wx.RIGHT|wx.LEFT, border=5)
        sizer.Add(hbox, pos=(5, 0), span=(1, 3), flag=wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM|wx.TOP, border=10)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableCol(1)
        sizer.AddGrowableCol(2)
        self.panel.SetSizerAndFit(sizer)

    def OnSaveRecord(self, event):

        if self.add_record:
            self.add_batch()
        else:
            self.edit_batch()

    def add_batch(self):
        """
        Add a new Batch record to the database.
        """

        data = self.get_data()
        add_batch_record(self.session, data)
        dialogs.show_message_dlg("Batch record added", "Success!", wx.OK|wx.ICON_INFORMATION)

        # clear the TextCtrls to add a new record
        for child in self.panel.GetChildren():
            if isinstance(child, wx.TextCtrl):
                child.SetValue("")
            if isinstance(child, wx.Choice):
                child.SetSelection(-1)

    def edit_batch(self):
        """
        Edit/Modify an existing Batch record in the database.
        """

        data = self.get_data()
        modify_batch_record(self.session, self.record.id, data)
        dialogs.show_message_dlg("Batch record modified", "Success!", wx.OK|wx.ICON_INFORMATION)
        self.Destroy()


    def get_data(self):

        if self.ch_chemical.GetSelection() < 0:
            wx.MessageBox("No Chemical selected", "Error!", style=wx.ICON_ERROR)
            return
        else:
            chemical_id = self.chemicals[self.ch_chemical.GetSelection()].id
        if self.ch_component.GetSelection() < 0:
            wx.MessageBox("No Component selected", "Error!", style=wx.ICON_ERROR)
            return
        else:
            component_id = self.components[self.ch_component.GetSelection()].id

        coefficient = self.txtc_coeff.GetValue()
        if coefficient != "":
            try:
                coefficient = float(coefficient)
            except:
                wx.MessageBox("Coefficient must be a number", "Error!", style=wx.ICON_ERROR)
                self.txtc_coeff.SetBackgroundColour("pink")
                self.txtc_coeff.SetFocus()
                self.txtc_coeff.Refresh()
                return
            self.txtc_coeff.SetBackgroundColour("white")
            self.txtc_coeff.Refresh()
        else:
            wx.MessageBox("No coefficient entered", "Error!", style=wx.ICON_ERROR)
            self.txtc_coeff.SetBackgroundColour("pink")
            self.txtc_coeff.SetFocus()
            self.txtc_coeff.Refresh()
            return

        if self.ch_reaction.GetSelection() < 0:
            reaction_id = None
        else:
            reaction_id = self.reactions[self.ch_reaction.GetSelection()].id

        data = {
            "chemical_id"  : chemical_id,
            "component_id" : component_id,
            "coefficient"  : coefficient,
            "reaction_id"  : reaction_id,
        }

        return data

    def OnClose(self, event):
        self.Destroy()

class AddModifyChemicalRecordDialog(wx.Dialog):

    def __init__(self, parent, session=None, record=None, title="Add", add_record=True,
            pos=wx.DefaultPosition, size=(400, 480)):

        super(AddModifyChemicalRecordDialog, self).__init__(parent, id=wx.ID_ANY, title="{0:s} a Chemical Record".format(title), size=size)

        self.panel = wx.Panel(self)

        # attributes
        self.session = session
        self.record = record
        self.add_record = add_record
        if record is not None:
            v_name = record.name
            v_formula = record.formula
            v_molwt = "{0:8.4f}".format(record.molwt)
            v_concentration = "{0:7.3f}".format(record.concentration)
            if record.short_name is not None:
                v_short_name = record.short_name
            else:
                v_short_name = ""
            if record.cas is not None:
                v_cas = record.cas
            else:
                v_cas = ""
            if record.density is not None:
                v_density = "{0:7.3f}".format(record.density)
            else:
                v_density = ""
            if record.pk is not None:
                v_pk = "{0:7.3f}".format(record.pk)
            else:
                v_pk = ""
            if record.smiles is not None:
                v_smiles = record.smiles
            else:
                v_smiles = ""
        else:
            v_name = v_formula = v_molwt = v_short_name = ""
            v_concentration = v_cas = v_density = v_pk = v_smiles = ""

        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)

        lbl_title = wx.StaticText(self.panel, -1, "{0:s} a Chemical Record".format(title))
        lbl_title.SetFont(font)
        lbl_name = wx.StaticText(self.panel, -1, "Name")
        lbl_formula = wx.StaticText(self.panel, -1, "Formula")
        lbl_molwt = wx.StaticText(self.panel, -1, "Molecular Weight")
        lbl_shname = wx.StaticText(self.panel, -1, "Short Name")
        lbl_conc = wx.StaticText(self.panel, -1, "Concentration")
        lbl_cas = wx.StaticText(self.panel, -1, "CAS")
        lbl_density = wx.StaticText(self.panel, -1, "Density")
        lbl_pk = wx.StaticText(self.panel, -1, "pK")
        lbl_smiles = wx.StaticText(self.panel, -1, "SMILES")
        lbl_kind = wx.StaticText(self.panel, -1, "Kind")
        lbl_form = wx.StaticText(self.panel, -1, "Physical Form")
        lbl_elect = wx.StaticText(self.panel, -1, "Electrolyte")

        self.txtc_name = wx.TextCtrl(self.panel, -1, v_name)
        self.txtc_formula = wx.TextCtrl(self.panel, -1, v_formula)
        self.txtc_molwt = wx.TextCtrl(self.panel, -1, v_molwt, style=wx.TE_RIGHT)
        self.txtc_shname = wx.TextCtrl(self.panel, -1, v_short_name)
        self.txtc_conc = wx.TextCtrl(self.panel, -1, v_concentration)
        self.txtc_cas = wx.TextCtrl(self.panel, -1, v_cas)
        self.txtc_density = wx.TextCtrl(self.panel, -1, v_density)
        self.txtc_pk = wx.TextCtrl(self.panel, -1, v_pk)
        self.txtc_smiles = wx.TextCtrl(self.panel, -1, v_smiles)

        kinds = parent.model.get_kinds()
        kind_choices = ["Undefined"] + [x.name for x in kinds]
        forms = parent.model.get_physical_forms()
        form_choices = ["Undefined"] + [x.form for x in forms]
        elecs = parent.model.get_electrolytes()
        elec_choices = ["Undefined"] + [x.name for x in elecs]

        self.ch_kind = wx.Choice(self.panel, -1, size=(80, -1), choices=kind_choices)
        self.ch_form = wx.Choice(self.panel, -1, size=(80, -1), choices=form_choices)
        self.ch_elects = wx.Choice(self.panel, -1, size=(80, -1), choices=elec_choices)

        if record is not None:
            if self.record.kind is not None:
                self.ch_kind.SetStringSelection(self.record.kind)
            else:
                self.ch_kind.SetSelection(0)
            if self.record.physical_form is not None:
                self.ch_form.SetStringSelection(self.record.physical_form)
            else:
                self.ch_form.SetSelection(0)
            if self.record.electrolyte is not None:
                self.ch_elects.SetStringSelection(self.record.electrolyte)
            else:
                self.ch_elects.SetSelection(0)
        else:
                self.ch_kind.SetSelection(0)
                self.ch_form.SetSelection(0)
                self.ch_elects.SetSelection(0)


        sizer = wx.GridBagSizer(vgap=5, hgap=5)
        sizer.Add(lbl_title,   pos=( 0, 0), span=(1, 2), flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, border=10)
        sizer.Add(lbl_name,    pos=( 1, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_formula, pos=( 2, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_molwt,   pos=( 3, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_shname,  pos=( 4, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_conc,    pos=( 5, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_cas,     pos=( 6, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_density, pos=( 7, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_pk,      pos=( 8, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_smiles,  pos=( 9, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_kind,    pos=(10, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_form,    pos=(11, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_elect,   pos=(12, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)

        sizer.Add(self.txtc_name,    pos=( 1, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_formula, pos=( 2, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_molwt,   pos=( 3, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_shname,  pos=( 4, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_conc,    pos=( 5, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_cas,     pos=( 6, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_density, pos=( 7, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_pk,      pos=( 8, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_smiles,  pos=( 9, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.ch_kind,      pos=(10, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.ch_form,      pos=(11, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.ch_elects,    pos=(12, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)

        buttonOk = wx.Button(self.panel, id=wx.ID_ANY, label="{0:s}".format(title))
        buttonOk.SetDefault()
        buttonOk.Bind(wx.EVT_BUTTON, self.OnSaveRecord)
        buttonCancel = wx.Button(self.panel, id=wx.ID_CANCEL)
        buttonCancel.Bind(wx.EVT_BUTTON, self.OnClose)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(buttonOk, flag=wx.RIGHT|wx.LEFT, border=5)
        hbox.Add(buttonCancel, flag=wx.RIGHT|wx.LEFT, border=5)
        sizer.Add(hbox, pos=(13, 0), span=(1, 2), flag=wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM|wx.TOP, border=5)

        sizer.AddGrowableCol(1)
        self.panel.SetSizerAndFit(sizer)

    def is_empty(self, textctrl, message):

        if len(textctrl.GetValue()) == 0:
            wx.MessageBox(message, "Error")
            textctrl.SetBackgroundColour("pink")
            textctrl.SetFocus()
            textctrl.Refresh()
            return True
        else:
            textctrl.SetBackgroundColour("white")
            textctrl.Refresh()

    def is_number(self, textctrl, message):

        try:
            float(textctrl.GetValue())
            textctrl.SetBackgroundColour("white")
            textctrl.Refresh()
            return True
        except:
            wx.MessageBox(message, "Error")
            textctrl.SetBackgroundColour("pink")
            textctrl.SetFocus()
            textctrl.Refresh()
            return False

    def add_chemical(self):

        if self.is_empty(self.txtc_name, "Name of the Chemical is required"):
            return

        if self.is_empty(self.txtc_formula, "Formula of the Chemical is required"):
            return

        if self.is_empty(self.txtc_molwt, "Molecular weight of the Chemical is required"):
            return
        else:
            if not self.is_number(self.txtc_molwt, "Molecular weight must be a number"):
                return

        if self.is_empty(self.txtc_conc, "Concentration of the Chemical is required"):
            return
        else:
            if not self.is_number(self.txtc_conc, "Concentration must be a number"):
                return

        if self.txtc_density.GetValue() != "":
            if not self.is_number(self.txtc_density, "Density must be a number"):
                return

        if self.txtc_pk.GetValue() != "":
            if not self.is_number(self.txtc_pk, "pK must be a number"):
                return

        if self.ch_kind.GetStringSelection() == "Undefined":
            wx.MessageBox("Please select the Kind", "Error")
            return

        data = self.get_data()

        add_chemical_record(self.session, data)

        dialogs.show_message_dlg("Chemical added", "Success!", wx.OK|wx.ICON_INFORMATION)

        # clear the TextCtrls to add a new record
        for child in self.panel.GetChildren():
            if isinstance(child, wx.TextCtrl):
                child.SetValue("")
            if isinstance(child, wx.Choice):
                child.SetSelection(0)

    def edit_chemical(self):

        if self.is_empty(self.txtc_name, "Name of the Chemical is required"):
            return

        if self.is_empty(self.txtc_formula, "Formula of the Chemical is required"):
            return

        if self.is_empty(self.txtc_molwt, "Molecular weight of the Chemical is required"):
            return
        else:
            if not self.is_number(self.txtc_molwt, "Molecular weight must be a number"):
                return

        if self.is_empty(self.txtc_conc, "Concentration of the Chemical is required"):
            return
        else:
            if not self.is_number(self.txtc_conc, "Concentration must be a number"):
                return

        if self.ch_kind.GetStringSelection() == "Undefined":
            wx.MessageBox("Please select the Kind", "Error")
            return

        data = self.get_data()
        modify_chemical_record(self.session, self.record.id, data)
        self.Destroy()

    def OnSaveRecord(self, event):

        if self.add_record:
            self.add_chemical()
        else:
            self.edit_chemical()

    def OnClose(self, event):
        self.Destroy()

    def get_data(self):
        '''
        Retrieve the data from the dialogs' TextCtrls and ChoiceBoxes
        and return as a dictionary.
        '''

        chem_dict = {
            "name"          : self.txtc_name.GetValue(),
            "formula"       : self.txtc_formula.GetValue(),
            "molwt"         : self.txtc_molwt.GetValue(),
            "short_name"    : self.txtc_shname.GetValue(),
            "concentration" : self.txtc_conc.GetValue(),
            "cas"           : self.txtc_cas.GetValue(),
            "density"       : self.txtc_density.GetValue(),
            "pk"            : self.txtc_pk.GetValue(),
            "smiles"        : self.txtc_smiles.GetValue(),
            "kind"          : self.ch_kind.GetStringSelection(),
            "electrolyte"   : self.ch_elects.GetStringSelection(),
            "physical_form" : self.ch_form.GetStringSelection(),
        }

        return chem_dict

class AddModifyComponentRecordDialog(wx.Dialog):

    def __init__(self, parent, session=None, record=None, title="Add", add_record=True,
            pos=wx.DefaultPosition, size=(400, 270)):

        super(AddModifyComponentRecordDialog, self).__init__(parent, id=wx.ID_ANY, title="{0:s} a Component Record".format(title), size=size)

        self.panel = wx.Panel(self)

        # attributes
        self.session = session
        self.record = record
        self.add_record = add_record
        if record is not None:
            v_name = record.name
            v_formula = record.formula
            v_molwt = "{0:8.4f}".format(record.molwt)
            v_shname = record.short_name
        else:
            v_name = v_formula = v_molwt = v_shname = ""

        font = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)

        lbl_title = wx.StaticText(self.panel, -1, "{0:s} Component Record".format(title))
        lbl_title.SetFont(font)
        lbl_name = wx.StaticText(self.panel, -1, "Name")
        lbl_formula = wx.StaticText(self.panel, -1, "Formula")
        lbl_molwt = wx.StaticText(self.panel, -1, "Molecular Weight")
        lbl_shname = wx.StaticText(self.panel, -1, "Short Name")
        lbl_category = wx.StaticText(self.panel, -1, "Category")

        self.txtc_name = wx.TextCtrl(self.panel, -1, v_name)
        self.txtc_formula = wx.TextCtrl(self.panel, -1, v_formula)
        self.txtc_molwt = wx.TextCtrl(self.panel, -1, v_molwt)
        self.txtc_shname = wx.TextCtrl(self.panel, -1, v_shname)

        categ = parent.model.get_categories()
        categ_choices = ["Undefined"] + [x.name for x in categ]

        self.ch_category = wx.Choice(self.panel, -1, (100, 50), choices=categ_choices)

        if record is not None:
            if self.record.category is not None:
                self.ch_category.SetStringSelection(self.record.category)
            else:
                self.ch_category.SetSelection(0)
        else:
            self.ch_category.SetSelection(0)

        sizer = wx.GridBagSizer(vgap=5, hgap=5)
        sizer.Add(lbl_title,    pos=(0, 0), span=(1, 2), flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, border=10)
        sizer.Add(lbl_name,     pos=(1, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_formula,  pos=(2, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_molwt,    pos=(3, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_shname,   pos=(4, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)
        sizer.Add(lbl_category, pos=(5, 0), span=(1, 1), flag=wx.LEFT|wx.RIGHT, border=10)

        sizer.Add(self.txtc_name,    pos=(1, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_formula, pos=(2, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_molwt,   pos=(3, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.txtc_shname,  pos=(4, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)
        sizer.Add(self.ch_category,  pos=(5, 1), span=(1, 1), flag=wx.LEFT|wx.EXPAND|wx.RIGHT, border=10)

        buttonOk = wx.Button(self.panel, id=wx.ID_ANY, label="{0:s}".format(title))
        buttonOk.SetDefault()
        buttonOk.Bind(wx.EVT_BUTTON, self.OnSaveRecord)
        buttonCancel = wx.Button(self.panel, id=wx.ID_CANCEL)
        buttonCancel.Bind(wx.EVT_BUTTON, self.OnClose)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(buttonOk, flag=wx.RIGHT|wx.LEFT, border=5)
        hbox.Add(buttonCancel, flag=wx.RIGHT|wx.LEFT, border=5)
        sizer.Add(hbox, pos=(6, 0), span=(1, 2), flag=wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM|wx.TOP, border=5)

        sizer.AddGrowableCol(1)
        self.panel.SetSizerAndFit(sizer)

    def is_empty(self, textctrl, message):

        if len(textctrl.GetValue()) == 0:
            wx.MessageBox(message, "Error")
            textctrl.SetBackgroundColour("pink")
            textctrl.SetFocus()
            textctrl.Refresh()
            return True
        else:
            textctrl.SetBackgroundColour("white")
            textctrl.Refresh()

    def is_number(self, textctrl, message):

        try:
            float(textctrl.GetValue())
            textctrl.SetBackgroundColour("white")
            textctrl.Refresh()
            return True
        except:
            wx.MessageBox(message, "Error")
            textctrl.SetBackgroundColour("pink")
            textctrl.SetFocus()
            textctrl.Refresh()
            return False

    def OnSaveRecord(self, event):

        if self.add_record:
            self.add_component()
        else:
            self.edit_component()

    def add_component(self):

        if self.is_empty(self.txtc_name, "Name of the Component is required"):
            return

        if self.is_empty(self.txtc_formula, "Formula of the Component is required"):
            return

        if self.is_empty(self.txtc_molwt, "Molecular weight of the Component is required"):
            return
        else:
            if not self.is_number(self.txtc_molwt, "Molecular weight must be a number"):
                return

        if self.ch_category.GetStringSelection() == "Undefined":
            wx.MessageBox("Please select the Category", "Error")
            return

        data = self.get_data()

        add_component_record(self.session, data)

        dialogs.show_message_dlg("Component added", "Success!", wx.OK|wx.ICON_INFORMATION)

        # clear the TextCtrls to add a new record
        for child in self.panel.GetChildren():
            if isinstance(child, wx.TextCtrl):
                child.SetValue("")
            if isinstance(child, wx.Choice):
                child.SetSelection(0)

    def edit_component(self):

        if self.is_empty(self.txtc_name, "Name of the Component is required"):
            return

        if self.is_empty(self.txtc_formula, "Formula of the Component is required"):
            return

        if self.is_empty(self.txtc_molwt, "Molecular weight of the Component is required"):
            return
        else:
            if not self.is_number(self.txtc_molwt, "Molecular weight must be a number"):
                return

        if self.ch_category.GetStringSelection() == "Undefined":
            wx.MessageBox("Please select the Category", "Error")
            return

        data = self.get_data()

        modify_component_record(self.session, self.record.id, data)
        dialogs.show_message_dlg("Component modified", "Success!", wx.OK|wx.ICON_INFORMATION)

        self.Destroy()

    def OnClose(self, event):
        self.Destroy()

    def get_data(self):

        comp_dict = {
            "name"          : self.txtc_name.GetValue(),
            "formula"       : self.txtc_formula.GetValue(),
            "molwt"         : self.txtc_molwt.GetValue(),
            "short_name"    : self.txtc_shname.GetValue(),
            "category"      : self.ch_category.GetStringSelection(),
        }

        return comp_dict

def print_attrs(inst):

    print "Class {0}".format(inst.__class__.__name__)
    for key in sorted(inst.__dict__.keys()):
        if not key.startswith("_"):
            print "{0:s} : {1:s}".format(key, str(getattr(inst, key)))

################################################################################
# controller methods
################################################################################

########## Batch controller methods

def add_batch_record(session, data):
    """
    Add a Batch record to the database, the data should be in the form of a dictionary:

    data = {'chemical_id' : '1', 'component_id' : '1', 'coefficient' : 0.5,
            'reaction_id' : 3,}
    """

    batch = Batch(**data)
    session.add(batch)
    session.commit()

def delete_batch_record(session, id_num):
    """
    Delete an exisitng Batch record.
    """

    batch = session.query(Batch).get(id_num)
    session.delete(batch)
    session.commit()

def modify_batch_record(session, id_num, data):
    """
    Edit/Modify an existing Batch record.
    """

    batch = session.query(Batch).get(id_num)
    batch.coefficient = data['coefficient']
    if data['chemical_id'] is not None:
        batch._chemical = session.query(Chemical).get(data['chemical_id'])
    if data['component_id'] is not None:
        batch._component = session.query(Component).get(data['component_id'])
    if data['reaction_id'] is not None:
        batch._reaction = session.query(Reaction).get(data['reaction_id'])
    session.add(batch)
    session.commit()

########## Chemical controller methods

def add_chemical_record(session, data):
    """
    Add a Chemical record to the database, the data should be in the form of a dictionary:

    data = {'name' : 'water', 'formula' : 'H2O', 'molwt' : 18.0152,
            '_kind_id' : 3, 'concentration' : 1.0, 'cas' : '7732-18-5',
            '_physical_form_id' : 3, 'density' : 0.997}
    """

    kind = data.pop("kind", None)
    electrolyte = data.pop("electrolyte", None)
    if electrolyte == "Undefined":
        electrolyte = None
    physical_form = data.pop("physical_form", None)
    if physical_form == "Undefined":
        physical_form = None

    for k, v in data.items():
        if v == "":
            data[k] = None

    chemical = Chemical(**data)
    chemical._kind = session.query(Kind).filter(Kind.name == kind).one()

    if physical_form is not None:
        chemical._physical_form = session.query(PhysicalForm).filter(PhysicalForm.form == physical_form).one()

    if electrolyte is not None:
        chemical._electrolyte = session.query(Electrolyte).filter(Electrolyte.name == electrolyte).one()

    session.add(chemical)
    session.commit()

def delete_chemical_record(session, id_num):
    """
    Delete a Chemical record.
    """

    chemical = session.query(Chemical).get(id_num)
    session.delete(chemical)
    session.commit()

def modify_chemical_record(session, id_num, data):
    """
    Edit/Modify Chemical record in the database,
    """

    kind = data.pop("kind", None)
    electrolyte = data.pop("electrolyte", None)
    if electrolyte == "Undefined":
        electrolyte = None
    physical_form = data.pop("physical_form", None)
    if physical_form == "Undefined":
        physical_form = None

    for k, v in data.items():
        if v == "":
            data[k] = None
        setattr(chemical, k, data[k])

    chemical = session.query(Chemical).get(id_num)
    chemical._kind = session.query(Kind).filter(Kind.name == kind).one()

    if physical_form is not None:
        chemical._physical_form = session.query(PhysicalForm).filter(PhysicalForm.form == physical_form).one()

    if electrolyte is not None:
        chemical._electrolyte = session.query(Electrolyte).filter(Electrolyte.name == electrolyte).one()

    session.add(chemical)
    session.commit()

########## Compoment controller methods

def add_component_record(session, data):
    """
    Add a Component record to the database, the data should be in the form of a dictionary:

    data = {'name' : 'water', 'formula' : 'H2O', 'molwt' : 18.0152,
            '_catgory_id' : 3, 'short_name' : ''}
    """

    category = data.pop("category", None)
    if category == "Undefined":
        category = None

    component = Component(**data)

    if category is not None:
        component._category = session.query(Category).filter(Category.name == category).one()

    session.add(component)
    session.commit()

def delete_component_record(session, id_num):
    """
    Delete a Component record.
    """

    component = session.query(Component).get(id_num)
    session.delete(component)
    session.commit()

def modify_component_record(session, id_num, data):
    """
    Edit/Modify Component record in the database,
    """

    category = data.pop("category", None)
    if category == "Undefined":
        category = None

    component = session.query(Component).get(id_num)

    for k in data.keys():
        setattr(component, k, data[k])

    if category is not None:
        component._category = session.query(Category).filter(Category.name == category).one()

    session.add(component)
    session.commit()

########## Reaction controller methods

def add_reaction_record(session, data):

    reaction = Reaction(reaction=data)
    session.add(reaction)
    session.commit()

def delete_reaction_record(session, id_num):
    """
    Delete a Reaction record.
    """

    reaction = session.query(Reaction).get(id_num)
    session.delete(reaction)
    session.commit()

def modify_reaction_record(session, id_num, data):
    """
    Modify/Edit an existing Reaction record in the database
    """

    reaction = session.query(Reaction).get(id_num)
    reaction.reaction = data
    session.add(reaction)
    session.commit()

########## Category controller methods

def add_category_record(session, data):

    category = Category(name=data)
    session.add(category)
    session.commit()

def delete_category_record(session, id_num):
    """
    Delete a category record.
    """

    category = session.query(Category).get(id_num)
    session.delete(category)
    session.commit()

def modify_category_record(session, id_num, data):
    """
    Modify/Edit an existing Category record in the database
    """

    category = session.query(Category).get(id_num)
    category.name = data
    session.add(category)
    session.commit()

########## Kinds controller methods

def fill_kinds_table(session):
    """
    Fill the kinds table with allowed values
    """

    kinds = ["mixture", "solution", "reactant"]

    for kind in kinds:
        add_kind_record(session, kind)

def add_kind_record(session, data):
    """
    Add a Kind record.
    """

    kind = Kind(name=data)
    session.add(kind)
    session.commit()

def delete_kind_record(session, id_num):
    """
    Delete a Kind record.
    """

    kind = session.query(Kind).get(id_num)
    session.delete(kind)
    session.commit()

def modify_kind_record(session, id_num, data):
    """
    Modify/Edit an existing Kind record in the database
    """

    kind = session.query(Kind).get(id_num)
    kind.name = data
    session.add(kind)
    session.commit()

########## Physical_forms controller methods

def fill_physical_forms_table(session):
    """
    Fill the physical_forms table with allowed values
    """

    phfs = ["crystals", "solid", "liquid", "gas"]

    for phf in phfs:
        add_physical_form_record(session, phf)

def add_physical_form_record(session, data):
    """
    Add a PhysicalForm record.
    """

    phf = PhysicalForm(form=data)
    session.add(phf)
    session.commit()

def delete_physical_form_record(session, id_num):
    """
    Delete a PhysicalForm record.
    """

    phf = session.query(PhysicalForm).get(id_num)
    session.delete(phf)
    session.commit()

def modify_physical_form_record(session, id_num, data):
    """
    Modify/Edit an existing PhysicalForm record in the database
    """

    phf = session.query(PhysicalForm).get(id_num)
    phf.form = data
    session.add(phf)
    session.commit()

########## Electrolyte controller methods

def fill_electrolytes_table(session):
    """
    Fill the electrolyte table with allowed values
    """

    elecs = ["nonelectrolyte", "strong acid", "strong base", "weak acid", "weak base"]

    for elec in elecs:
        add_electrolyte_record(session, elec)

def add_electrolyte_record(session, data):
    """
    Add a Electrolyte record.
    """

    elec = Electrolyte(name=data)
    session.add(elec)
    session.commit()

def delete_electrolyte_record(session, id_num):
    """
    Delete a Electrolyte record.
    """

    elec = session.query(Electrolyte).get(id_num)
    session.delete(elec)
    session.commit()

def modify_electrolyte_record(session, id_num, data):
    """
    Modify/Edit an existing Eelectrolyte record in the database
    """

    elec = session.query(Electrolyte).get(id_num)
    elec.name = data
    session.add(elec)
    session.commit()
