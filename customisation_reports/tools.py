# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

import frappe
import sys
from frappe.modules.utils import export_customizations


def save_all_customisations(module):
	"Merges any possible customisations before saving them out to the supplied custom module"
	# get modules in custom apps
	custom_modules = [x[0] for x in frappe.db.get_all('Module Def', filters={'app_name': ('not in', ('frappe', 'erpnext'))}, fields=['name'], as_list=True)]

	if module not in custom_modules:
		raise ValueError(f'{module} not in custom modules: {custom_modules}')

	# get doctypes in the modules
	custom_doctypes = []
	for mod in custom_modules:
		custom_doctypes += [x[0] for x in frappe.db.get_all('DocType', filters={'module': mod}, fields=['name'], as_list=True)]

	# Go through all the customisations saving them
	saved_mode = frappe.conf.developer_mode
	frappe.conf.developer_mode = 1
	customisation_dts = [x[0] for x in frappe.db.get_all('DocField', filters={'fieldtype': 'Link', 'options': 'Module Def'}, fields=['parent'], as_list=True)]
	for custom in customisation_dts:
		if custom == 'DocType':
			# Merge the custom fields and property setters back into custom doctypes before saving all doctype customisations
			# TODO: support DocType Layout merge (v13)
			for dt in custom_doctypes:
				for cf, insert_after in frappe.db.get_all('Custom Field',
					filters={'dt': dt, 'options': ('!=', 'Workflow State')},
					fields=['name', 'insert_after'], as_list=True):
					merge_custom_field(cf, insert_after, dt)

				pss = frappe.db.get_all('Property Setter',
					filters={'doc_type': dt, 'property': ('!=', 'default_print_format')},
					fields=['name'], as_list=True)
				merge_property_setters(pss, dt)

			for dt in custom_doctypes:
				# Save custom doctypes to module
				frappe.get_doc('DocType', dt).save()
			for (dt,) in frappe.get_all('DocType', fields=['name'], as_list=True):
				# Save ALL doctype customisations to module
				export_customizations(module, dt, sync_on_migrate=1, with_permissions=1)

		elif custom in ('Data Migration Plan',):
			# Ignore
			pass
		else:
			print(f'Error: Customisation not saved: {custom}', file=sys.stderr)
	frappe.conf.developer_mode = saved_mode


def merge_custom_field(field, insert_after, doctype):
	"""
	Adds the custom field in the correct place in the doctype and removes the custom field
	Recursive because the insert_after might also be a Custom Field, so there is an order
	that they can be merged
	"""
	# Ignore if already merged
	try:
		cf = frappe.get_doc('Custom Field', field).as_dict()
	except frappe.DoesNotExistError:
		return
	if frappe.db.count('DocField', {'parent': doctype, 'fieldname': cf['fieldname']}):
		return

	if insert_after:
		prev = frappe.db.get_all('Custom Field',
			filters={'dt': doctype, 'fieldname': insert_after},
			fields=['name', 'insert_after'], as_list=True)
		is_in_dt = frappe.db.count('DocField', {'parent': doctype, 'fieldname': insert_after})

		# Recurse if insert_after is another custom field
		if prev:
			prev_cf, prev_cf_insert_after = prev[0]
			merge_custom_field(prev_cf, prev_cf_insert_after, doctype)
		# Able to insert into doctype
		elif is_in_dt:
			pass
		# insert_after doesn't exist?
		else:
			raise ValueError(f"Custom Field '{field}' insert after '{insert_after}' doesn't exist")
	# Empty insert_after will be inserted at the beginning

	print(f"Merging Custom Field '{field}' after '{cf['insert_after']}'")
	dt = frappe.get_doc('DocType', doctype)
	cf['doctype'] = 'DocField'
	del cf['name']
	del cf['idx']
	del cf['dt']
	del cf['insert_after']

	fields = dt.fields
	dt.set('fields', [])
	found = False
	for f in fields:
		# append will reset the idx but only if it's zero
		f.idx = 0
		if not insert_after and not found:
			found = dt.append('fields', cf)
		dt.append('fields', f)
		if insert_after == f.fieldname:
			found = dt.append('fields', cf)

	dt.save()
	frappe.delete_doc('Custom Field', field)
	frappe.db.commit()

def merge_property_setters(setters, doctype):
	"Straight overwrite of DocType/Field properties. If the DocField is not found the property setter will be removed"
	dt = frappe.get_doc('DocType', doctype)
	for (setter,) in setters:
		ps = frappe.get_doc('Property Setter', setter)
		print(f"Merging Property Setter '{setter}' into '{ps.doctype_or_field}' of '{doctype}'")

		object = None
		if ps.doctype_or_field == 'DocField':
			for f in dt.fields:
				if f.fieldname == ps.field_name:
					object = f
					break
			else:
				print('  Warning: DocField not found, removing Property Setter with no action')
		else:
			object = dt

		if object:
			value = frappe.format_value(ps.value, df=ps.property_type)
			object.set(ps.property, value)

		frappe.delete_doc('Property Setter', setter)

	dt.save()
	frappe.db.commit()

# save out all customisations:
#(('Print Format',), ('Notification',), ('Report',), ('Web Form',), ('Website Theme',), ('Page',), ('Data Migration Plan',), ('DocType',))
