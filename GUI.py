# LIPGLOSS - Graphical user interface for constructing glaze recipes
# Copyright (C) 2017 Pieter Mostert

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# version 3 along with this program (see LICENCE.txt).  If not, see
# <http://www.gnu.org/licenses/>.

# Contact: pi.mostert@gmail.com

import tkinter.messagebox
from numbers import Number

from recipes import *
from polyplot import *

## SECTION 1
# Create stuff for restriction window

# oxides

entry_type = StringVar()

def update_oxide_entry_type(recipe, entry_type):

    global current_recipe
    current_recipe.update_oxides()

    for et in ['umf_', 'mass_perc_', 'mole_perc_']:
        if et == entry_type:
            for ox in current_recipe.oxides:
                restr_dict[et+ox].display(1 + oxide_dict[ox].pos)
        else:
            for ox in current_recipe.oxides:
                restr_dict[et+ox].hide()

# SECTION 2
# Selecting variables for 2 dim projection

def update_var(recipe, restr, t, event):  # t should be either 'x' or 'y'. Might be a better way of doing this
    if t in recipe.variables:
        v = restr_dict[recipe.variables[t]]
        if v == restr:
            del recipe.variables[t]
            restr.deselect(t)
        else:
            recipe.variables[t] = restr.index
            v.deselect(t)
            restr.select(t)      
    else:
        recipe.variables[t] = restr.index
        restr.select(t)

def bind_restrictions_to_recipe(recipe, restr_dict):    #   Set the command for x and y variable selection boxes
    for index in restr_keys(oxide_dict, ingredient_dict, other_dict):
        restr = restr_dict[index]
        restr.left_label.bind("<Button-1>", partial(update_var, recipe, restr, 'x'))
        restr.right_label.bind("<Button-1>", partial(update_var, recipe, restr, 'y'))

# SECTION 3
# Functions relating to opening and saving recipes.

recipe_name = StringVar()
Label(recipe_name_frame, textvariable = recipe_name, font = ("Helvetica 12 italic")).grid()  # displays the name of the current recipe

def open_recipe(index, restr_dict, r_s=0):   # to be used when opening a recipe, (or when ingredients have been updated?). Be careful.

    global recipe_index
    global current_recipe
    recipe_index = index

    for t, res in current_recipe.variables.items():
        restr_dict[res].deselect(t)            # remove stars from old variables
    current_recipe = copy.deepcopy(recipe_dict[index])
    current_recipe.update_oxides()            # in case the oxide compositions have changed
    
    recipe_name.set(current_recipe.name)      # update the displayed recipe name

    #for i in restr_keys(oxide_dict, ingredient_dict, other_dict):
    for i in restr_dict:
        restr_dict[i].remove(current_recipe)    # clear the entries from previous recipes, if opening a new recipe

    for i in restr_keys(current_recipe.oxides, current_recipe.ingredients, current_recipe.other):
        try:
            restr_dict[i].low.set(current_recipe.lower_bounds[i])
            restr_dict[i].upp.set(current_recipe.upper_bounds[i])
        except:
            restr_dict[i].low.set(restr_dict[i].default_low)    # this is just for the case where the oxides have changed
            restr_dict[i].upp.set(restr_dict[i].default_upp)    # ditto

    for t, res in current_recipe.variables.items():
        restr_dict[res].select(t)               # add stars to new variables
    
    et = current_recipe.entry_type
    entry_type.set(et)

    for ox in current_recipe.oxides:
        restr_dict[et+ox].display(1 + oxide_dict[ox].pos)

    for i in ingredient_dict:
        if i in current_recipe.ingredients:
            ingredient_select_button[i].state(['pressed'])
            restr_dict['ingredient_'+i].display(101 + ingredient_dict[i].pos)
        else:
            ingredient_select_button[i].state(['!pressed'])

    for ot in other_dict:
        if ot in current_recipe.other:
            other_select_button[ot].state(['pressed'])
            restr_dict['other_'+ot].display(1001 + other_dict[ot].pos)
        else:
            other_select_button[ot].state(['!pressed'])

    try:
        r_s.destroy()
    except:
        pass
    bind_restrictions_to_recipe(current_recipe, restr_dict)

def display_recipe(index, frame, window):     # display recipe name in recipe_selector
    recipe = recipe_dict[index]
    name_button =  ttk.Button(master=frame, text = recipe.name, width=20,
                             command = partial(open_recipe, index, restr_dict, window))
    name_button.grid(row=recipe.pos+1, column=0)

def open_recipe_menu():   # Opens window that lets you select a recipe to open
    global recipe_selector
    global r_s_scrollframe

    recipe_selector = Toplevel()

    r_s_scrollframe = VerticalScrolledFrame(recipe_selector)
    r_s_scrollframe.frame_height = 200
    r_s_scrollframe.pack()
    recipe_selector_buttons = Frame(recipe_selector)
    recipe_selector_buttons.pack()

    Label(master=r_s_scrollframe.interior, text='Recipes', width=15).grid(row=0, column=1)  

    for index in recipe_dict:
        display_recipe(index, r_s_scrollframe.interior, recipe_selector) 
            
    r_s_scrollframe.interior.focus_force()

def update_shelf(name, dictionary):
    with shelve.open(name) as shelf:
        shelf = dictionary
        
def update_shelf_entry(name, key, value):
    with shelve.open(name) as shelf:
        shelf[key] = value
        
def save_recipe():
    global recipe_dict
    current_recipe.update_bounds(restr_dict)
    current_recipe.entry_type = entry_type.get()
    recipe_dict[recipe_index] = copy.deepcopy(current_recipe)
    update_shelf_entry("RecipeShelf", recipe_index, current_recipe)

def save_new_recipe():
    global recipe_index
    global recipe_dict
    current_recipe.update_bounds(restr_dict)
    current_recipe.entry_type = entry_type.get()
    with shelve.open("RecipeShelf") as Recipe_Shelf:
        r = max([int(index) for index in Recipe_Shelf]) + 1
        recipe_index = str(r)
        current_recipe.name = 'Recipe Bounds '+recipe_index
        current_recipe.pos = r
        Recipe_Shelf[recipe_index] = current_recipe
    recipe_dict[recipe_index] = copy.deepcopy(current_recipe)
    recipe_name.set(current_recipe.name)

# open first (default) recipe in list
with shelve.open("RecipeShelf") as Recipe_Shelf:
    recipe_dict = dict(Recipe_Shelf)
    current_recipe = recipe_dict['0']

# SECTION 4
# Options in the Options menu: Edit Oxides, Edit Ingredients, Edit Other Rrestricitons, Restriction Settings.
# Currently only Edit Ingredients does anything

# SECTION 4.1
# Come back to this later. Include the option to only display an oxide when at least one of the ingredients contains at
# least x% of that oxide, where x can be modified by the user. Might not include this at all.

def edit_oxides():
    pass                       

# SECTION 4.2
# Functions relating to the ingredient editor window (accessed through Options > Edit Ingredients)

def update_ingredient_dict():         # Run when updating ingredients. Needs improvement since it removes stars from
                                      # ingredients that correspond to x or y variables.

    global ingredient_dict
    global prob

    for index in ingredient_dict:
        ing = ingredient_dict[index]
        ing.name = ing.display_widgets['name'].get()
        restr_dict['ingredient_'+index].name = ing.name              # update restriction name
        restr_dict['ingredient_'+index].left_label_text.set(ing.name+' : ')
        restr_dict['ingredient_'+index].right_label_text.set(' : '+ing.name)
        ingredient_select_button[index].config(text = ing.name)
        for ox in oxides:
            try:
                val = eval(ing.display_widgets[ox].get())
            except:
                val = 0
            if isinstance(val,Number) and val != 0:
                ing.oxide_comp[ox] = val
            else:
                ing.display_widgets[ox].delete(0,END)
                try:
                    del ing.oxide_comp[ox]
                except:
                    pass

        for attr in other_attr_names:
            ing.other_attributes[attr] = ing.display_widgets[attr].get()

        ingredient_dict[index] = ing
    
    with shelve.open("IngredientShelf") as ingredient_shelf:
        for index in ingredient_shelf:
            ingredient_shelf[index] = ingredient_dict[index].pickleable_version()
    ingredient_compositions = get_ing_comp()
    
    #make this a function update_basic_constraints
    for ox in oxide_dict:
        prob.constraints[ox] = sum(ingredient_compositions[index][ox]*lp_var['ingredient_'+index]/100 \
                                   for index in ingredient_dict if ox in ingredient_compositions[index]) \
                               == lp_var['mass_'+ox]     # relate ingredients and oxides

def delete_ingredient(index):

    global ingredient_dict

    oxides_to_update = ingredient_dict[index].oxide_comp

    ingredient_compositions = get_ing_comp()   # shouldn't be necessary
    prob._variables.remove(lp_var['ingredient_'+index])     # somehow, this doesn't seem to be happening

    #make this a function update_basic_constraints
    for ox in oxides_to_update:
        prob.constraints[ox] = sum(ingredient_compositions[index][ox]*lp_var['ingredient_'+index]/100 \
                                   for index in ingredient_dict if ox in ingredient_compositions[index]) \
                               == lp_var['mass_'+ox]     # relate ingredients and oxides

    for widget in ['del', 'name'] + oxides + ['0', '1', '2']:
        ingredient_dict[index].display_widgets[widget].destroy()

    if index in current_recipe.ingredients:
        toggle_ingredient(index)

    del ingredient_dict[index]
    with shelve.open("IngredientShelf") as ingredient_shelf:
        del ingredient_shelf[index]
    
    ingredient_select_button[index].destroy()   # remove the deleted ingredient from the list of ingredients to select from
    
    try:
        del prob.constraints['ingredient_'+index+'_lower']  # Is this necessary?
    except:
        pass
    try:
        del prob.constraints['ingredient_'+index+'_upper']  # Is this necessary?
    except:
        pass
    prob.constraints['ing_total'] = lp_var['ingredient_total'] == sum(lp_var['ingredient_'+i] for i in ingredient_dict)

    del restr_dict['ingredient_'+index]
  
    # To Do: delete the ingredient from all recipes. If there are any recipes containing this ingredient, get confirmation from the user
    # before doing this
  
def new_ingredient():

    global ingredient_dict
    
    with shelve.open("IngredientShelf") as ingredient_shelf:
        r = max([int(index) for index in ingredient_shelf]) + 1
        index = str(r)
        ing = ingredient_shelf[str(r)] = Ingredient(r, 'Ingredient #'+index, notes = '', oxide_comp = {}, other_attributes = {'0':0, '1':0, '2':0})
                        # If we just had Ingredient(r, 'Ingredient #'+index) above, the default values of the notes, oxide_comp
                        # and other_attributes attributes would change when the last instance of the class defined had those
                        # attributes changed
##        ing = Ingredient(r, 'Ingredient #'+index, oxide_comp = {})
##        print(ing.oxide_comp)
##        print(ing.name)
##        ingredient_shelf[str(r)] = copy.deepcopy(ing)
    ingredient_dict[index] = ing

    lp_var['ingredient_'+index] = pulp.LpVariable('ingredient_'+index, 0, None, pulp.LpContinuous)
    prob.constraints['ing_total'] = lp_var['ingredient_total'] == sum(lp_var['ingredient_'+index] for index in ingredient_dict)
    
    ingredient_dict[index] = ing
    ing.display(index, i_e_scrollframe.interior, delete_ingredient)
    restr_dict['ingredient_'+index] = Restriction('ingredient_'+index, ing.name, 'ingredient_'+index, "0.01*lp_var['ingredient_total']", 0, 100)

    ingredient_select_button[index] = ttk.Button(vsf.interior, text = ing.name, width=20,
                                                 command = partial(toggle_ingredient, index))
    ingredient_select_button[index].grid(row = ing.pos)
    
    restr = restr_dict['ingredient_'+index]
    restr.left_label.bind("<Button-1>", partial(update_var, current_recipe, restr, 'x'))
    restr.right_label.bind("<Button-1>", partial(update_var, current_recipe, restr, 'y'))  

def edit_ingredients():   # Opens window that lets you add, delete, and edit oxide compositions of ingredients. Turn this into a class?
    global ingredient_dict   # Get rid of this eventually?
    global ingredient_editor
    global i_e_scrollframe

    try:
        ingredient_editor.winfo_exists()
        ingredient_editor.lift()
    except:
        ingredient_editor = Toplevel()
    
        i_e_scrollframe = VerticalScrolledFrame(ingredient_editor)
        i_e_scrollframe.frame_height = 500
        i_e_scrollframe.pack()
        ingredient_editor_buttons = Frame(ingredient_editor)
        ingredient_editor_buttons.pack()

        Label(master=i_e_scrollframe.interior, text='Ingredient', width=15).grid(row=0, column=1)

        c=3
        for ox in oxides:
            Label(master=i_e_scrollframe.interior, text=prettify(ox), width=5).grid(row=0, column=c)
            c+=1

        for i, attr in other_attr_names.items():
            Label(master=i_e_scrollframe.interior, text=attr, width=5).grid(row=0, column=c+int(i))   # replace int(i) by other_attr_dict[attr].pos
        
        for index in ingredient_dict:
                ingredient_dict[index].display(index, i_e_scrollframe.interior, delete_ingredient)  

        new_ingr_button = ttk.Button(ingredient_editor_buttons, text = 'New ingredient', width=20, command = new_ingredient)
        new_ingr_button.pack(side = 'left')   
        update_button = ttk.Button(ingredient_editor_buttons, text = 'Update', width=20, command = update_ingredient_dict)
        update_button.pack(side = 'right')

        i_e_scrollframe.interior.focus_force()

# SECTION 4.3
# Introduce the option of adding custom restrictions. Users will define the numerator and denominator, which will be linear
# combinations of the lp_var[] variables.

def edit_other_restrictions():
    pass                           

# SECTION 4.4
# Set default user lower and upper bounds for all restrictions, and rearrange the order in which they are listed (with each group).
# Also set the number of decimal places to display for calculated bounds
        
def restriction_settings():
    pass

# SECTION 5
# Create menus
file_menu = Menu(menubar, tearoff=0)    
file_menu.add_command(label="Open", command=open_recipe_menu)
file_menu.add_command(label="Save", command=save_recipe)
file_menu.add_command(label="Save as new recipe", command=save_new_recipe)
menubar.add_cascade(label="File", menu=file_menu)

option_menu.add_command(label="Edit Oxides", command=edit_oxides)
option_menu.add_command(label="Edit Ingredients", command=edit_ingredients)
option_menu.add_command(label="Edit Other Restricitions", command=edit_other_restrictions)
option_menu.add_command(label="Restriction Settings", command=restriction_settings)
menubar.add_cascade(label="Options", menu=option_menu)

# SECTION 6:
# defines structures for the window on the left which allows users to add and remove ingredients and other restrictions to the problem.

ingredient_select_button={}

def toggle_ingredient(index):     # adds or removes ingredient_dict[index] to or from the current recipe
                                  # depending on whether it isn't or is an ingredient already
    global current_recipe
    global ingredient_select_button
    ingredient_compositions = get_ing_comp()
    
    if index in current_recipe.ingredients:
        current_recipe.ingredients.remove(index)
        ingredient_select_button[index].state(['!pressed'])
        restr_dict['ingredient_'+index].remove(current_recipe)
        current_recipe.update_oxides()

##        if 'Na2O' in selected_oxides and 'K2O' in selected_oxides:
##            selected_oxides.add('KNaO')
            
        for ox in set(ingredient_compositions[index]) - current_recipe.oxides:
            for et in ['umf_', 'mass_perc_', 'mole_perc_']:
                restr_dict[et+ox].remove(current_recipe)                     # remove the restrictions on the oxides no longer present

    else:
        current_recipe.ingredients.append(index)
        ingredient_select_button[index].state(['pressed'])
        restr_dict['ingredient_'+index].display(101 + ingredient_dict[index].pos)
        current_recipe.oxides = current_recipe.oxides.union(set(ingredient_compositions[index]))    # update the available oxides
           
        et = entry_type.get()
        for ox in current_recipe.oxides:
            restr_dict[et+ox].display(1 + oxide_dict[ox].pos)

def grid_ingr_select_buttons(frame):
    global ingredient_select_button
    for child in frame.winfo_children():
        child.destroy()

    for index in ingredient_dict:
        ingredient_select_button[index] = ttk.Button(frame, text = ingredient_dict[index].name, width=20,
                                                     command = partial(toggle_ingredient, index))
        ingredient_select_button[index].grid(row = ingredient_dict[index].pos)

grid_ingr_select_buttons(vsf.interior)

# Other restrictions

other_select_button={}

def toggle_other(index):          # adds or removes other_dict[index] to or from the current recipe
                                   # depending on whether it isn't or is an other restriction already
    global current_recipe
    global other_select_button

    if index in current_recipe.other:
        current_recipe.other.remove(index)
        other_select_button[index].state(['!pressed'])
        restr_dict['other_'+index].remove(current_recipe)

    else:
        current_recipe.other.append(index)
        other_select_button[index].state(['pressed'])         
        restr_dict['other_'+index].display(1001 + other_dict[index].pos)

for index in other_dict:
    ot = other_dict[index]
    other_select_button[index] = ttk.Button(other_selection_window, text = prettify(ot.name),
                                               width=18, command = partial(toggle_other, index))
    other_select_button[index].grid(row = ot.pos+1) 

# SECTION 7
# Calculations. See the recipe_class file for definitions of calc_restrictions and calc_2d_projection

proj_frame = ttk.Frame(main_frame, padding=(15, 5, 10, 5))  # this just needs to have been defined somewhere

# when you click on 'Calculate restrictions' (calcButton), this happens:

def calc():

    root.lift()  # If this isn't here, the ingredient editor covers the main window whenever it's open. Sometimes it still does this.
                 # Don't ask me why.

    current_recipe.calc_restrictions(prob, lp_var, restr_dict, ttk.Frame(main_frame, padding=(15, 5, 10, 5)))

    global proj_frame
    try:
        proj_frame.grid_forget()
    except:
        pass
    if len(current_recipe.variables) == 2 and restr_dict[current_recipe.variables['x']].normalization == restr_dict[current_recipe.variables['y']].normalization:
        proj_frame = ttk.Frame(main_frame, padding=(15, 5, 10, 5))
        proj_frame.grid(column = 1, row = 1, rowspan=1000, sticky = 'nw')

    current_recipe.calc_2d_projection(prob, lp_var, proj_frame)
    
calc_button = ttk.Button(main_frame, text = 'Calculate restrictions', command = calc)   # Calc button

# SECTION 8
# Grid remaining widgets

# grid oxide part of restriction frame
oxide_heading_frame = ttk.Frame(restriction_sf.interior)
oxide_heading_frame.grid(row = 0, column = 0, columnspan = 7)
Label(oxide_heading_frame, text = 'Oxides', font = ('Helvetica', 12)).grid(column = 0, row = 0, columnspan = 3)

# Percent/unity radio buttons
unity_radio_button = Radiobutton(oxide_heading_frame, text="UMF", variable = entry_type, value = 'umf_',
                                 command = partial(update_oxide_entry_type, current_recipe, 'umf_'))
unity_radio_button.grid(column = 0, row = 1)

percent_wt_radio_button = Radiobutton(oxide_heading_frame, text="% weight", variable = entry_type, value = 'mass_perc_', \
                                      command = partial(update_oxide_entry_type, current_recipe, 'mass_perc_'))
percent_wt_radio_button.grid(column = 1, row = 1)

percent_mol_radio_button = Radiobutton(oxide_heading_frame, text="% mol", variable = entry_type, value = 'mole_perc_', \
                                       command = partial(update_oxide_entry_type, current_recipe, 'mole_perc_'))
percent_mol_radio_button.grid(column = 2, row = 1)

unity_radio_button.select()

# grid calc button
calc_button.grid()

# grid message frame. At the moment, this isn't used
message_frame.grid(row = 3)

# display first (default) recipe in list
open_recipe('0', restr_dict)
    
root.config(menu=menubar)

root.mainloop()
