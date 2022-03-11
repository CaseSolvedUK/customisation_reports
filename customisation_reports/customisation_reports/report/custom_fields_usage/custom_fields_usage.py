# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

cf_fields = {
	('Module Def',): ['app_name'],
	('DocType',): ['module', 'issingle'],
	('Custom Field',): ['dt', 'label', 'fieldname', 'fieldtype', 'name as custom_field_name']
}

def execute(filters=None):
	from pymysql import Error

	fieldstr = get_fieldstr(cf_fields)
	custom_fields = frappe.db.sql(f"""
		SELECT {fieldstr}
		FROM `tabCustom Field` cf
		LEFT JOIN `tabDocType` d ON cf.dt=d.name
		LEFT JOIN `tabModule Def` md ON d.module=md.module_name
/*		WHERE d.name='Delivery Note' AND cf.fieldname='payment_terms1'*/
		ORDER BY d.name asc
	""", as_dict=1)

	columns = get_columns(cf_fields)

	for row in custom_fields:
		dt = row.get('dt')
		fn = row.get('fieldname')
		try:
			# Not empty ?
			used = frappe.db.sql(f"""SELECT COUNT(*) FROM `tab{dt}` WHERE `{fn}` <> '' """, as_dict=0)[0][0]
			total = get_row_total(dt)
			error = ''
		except Error as e:
			used = 0
			total = 0
			if e.args[0] == 1054:
				error = e.args[1]
			elif row.get('issingle'):
				used = frappe.db.sql(f"""SELECT COUNT(*) FROM `tabSingles` WHERE doctype='{dt}' AND field='{fn}' AND value NOT IN ('', 0) """, as_dict=0)[0][0]
				total = 1
			else:
				raise
		row['used'] = used
		row['total'] = total
		row['usage'] = ((100 * used) / total) if used else 0.0
		row['error'] = error

	columns.append({"label": _("Used"), "fieldname": "used", "fieldtype": "Int"})
	columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int"})
	columns.append({"label": _("Usage"), "fieldname": "usage", "fieldtype": "Percent"})
	columns.append({"label": _("Error"), "fieldname": "error", "fieldtype": "Data"})

	return columns, custom_fields

total_rows = {}
def get_row_total(doctype):
	global total_rows
	if doctype not in total_rows:
		total = frappe.db.sql(f"""SELECT COUNT(*) FROM `tab{doctype}` """, as_dict=0)[0][0]
		total_rows[doctype] = total
	return total_rows[doctype]

def abbrev(dt):
	return ''.join(l[0].lower() for l in dt.split(' ')) + '.'

def doclist(dt, dfs):
	return [abbrev(dt) + f for f in dfs]

def as_split(fields):
	for field in fields:
		split = field.split(' as ')
		yield (split[0], split[1] if len(split) > 1 else split[0])

def coalesce(doctypes, fields):
	coalesce = []
	for name, new_name in as_split(fields):
		sharedfields = ', '.join(abbrev(dt) + name for dt in doctypes)
		coalesce += [f'coalesce({sharedfields}) as {new_name}']
	return coalesce

def get_fieldstr(fieldlist):
	fields = []
	for doctypes, docfields in fieldlist.items():
		if len(doctypes) == 1 or isinstance(doctypes[1], int):
			fields += doclist(doctypes[0], docfields)
		else:
			fields += coalesce(doctypes, docfields)
	return ', '.join(fields)

def get_columns(fieldlist):
	# use of a dict ensures duplicate columns are removed
	columns = {}
	for doctypes, docfields in fieldlist.items():
		fieldmap = {old_name: new_name for old_name, new_name in as_split(docfields)}
		for doctype in doctypes:
			if isinstance(doctype, int):
				break

			# get column field metadata from the db
			meta = frappe.get_meta(doctype)
			for old_name in fieldmap.keys():
				fieldmeta = None
				new_name = fieldmap[old_name]
				for db_field in meta.get('fields'):
					if db_field.fieldname == old_name:
						fieldmeta = {
							"label": _(db_field.label),
							"fieldname": new_name,
							"fieldtype": db_field.fieldtype,
							"options": db_field.options
						}
				# edit the columns to match the modified data
				col = modify_report_columns(doctype, new_name, fieldmeta)
				if col:
					columns[new_name] = col
	return list(columns.values())

def modify_report_columns(doctype, field, column):
	"Changes to match any data manipulation or missing column info"
	if doctype in ("Custom Field"):
		if field == "custom_field_name":
			return {"label": _("Custom Field Name"), "fieldname": "custom_field_name", "fieldtype": "Link", "options": "Custom Field"}
	return column
