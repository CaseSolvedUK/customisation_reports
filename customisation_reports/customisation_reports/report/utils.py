# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _

def process_filters(fieldstr, filters):
	fields = fieldstr.split(', ')
	remainder = filters.copy()
	where = []
	for filt_field, filt_value in filters.items():
		# TODO: scrub filt_value due to sql injection
		for old_name, new_name in as_split(fields):
			if '.' + filt_field in old_name:
				remainder.pop(filt_field)
				condition = ''
				if not where:
					condition += 'WHERE '
				condition += f"{old_name} LIKE '%{filt_value}%'"
				where.append(condition)
	return ' AND '.join(where), remainder

def abbrev(dt):
	return ''.join(l[0].lower() for l in dt.split(' ')) + '.'

def doclist(dt, dfs):
	return [abbrev(dt) + f for f in dfs]

def as_split(fields):
	for field in fields:
		split = field.lower().split(' as ')
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

def modify_report_columns(doctype, field, column):
	"Changes to match any data manipulation or missing column info"
	return column

def get_columns(fieldlist, modify_report_columns=modify_report_columns):
	"Get column info from frappe metadata"
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
					elif old_name == 'name':
						fieldmeta = {
							"label": _(doctype),
							"fieldname": new_name,
							"fieldtype": 'Link',
							"options": doctype
						}
				# edit the columns to match the modified data
				col = modify_report_columns(doctype, new_name, fieldmeta)
				if col:
					columns[new_name] = col
	return list(columns.values())
