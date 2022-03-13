# Copyright (c) 2022, CaseSolved and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from ..utils import *

dt_fields = {
	('Module Def',): ['app_name'],
	('DocType',): ['module', 'issingle', 'name as dt']
}

def execute(filters=None):
	# Get Doctypes list
	fieldstr = get_fieldstr(dt_fields)
	where_clause, remainder_filters = process_filters(fieldstr, filters)
	doctypes = frappe.db.sql(f"""
		SELECT {fieldstr}
		FROM `tabDocType` dt
		LEFT JOIN `tabModule Def` md ON dt.module=md.module_name
		{where_clause}
		ORDER BY dt.name asc
	""", as_dict=1)

	columns = get_columns(dt_fields)

	# Get row counts and merge with doctypes
	filtered = []
	for row in doctypes:
		dt = row.get('dt')
		if row.get('issingle'):
			total = 1 if frappe.db.exists(dt) else 0
		else:
			total = frappe.db.count(dt)
		row['total'] = total

		# Filters
		for filt_field, filt_value in remainder_filters.items():
			if filt_field == 'total' and filt_value:
				if not eval('total ' + filt_value):
					break
		else:
			filtered.append(row)

	columns.append({"label": _("Total Rows"), "fieldname": "total", "fieldtype": "Int"})

	return columns, filtered
