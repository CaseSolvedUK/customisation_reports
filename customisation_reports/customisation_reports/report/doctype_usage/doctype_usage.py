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
		FROM `tabDocType` d
		LEFT JOIN `tabModule Def` md ON d.module=md.module_name
		{where_clause}
		ORDER BY d.name asc
	""", as_dict=1)

	columns = get_columns(dt_fields)

	# Get row counts and merge with doctypes
	for row in doctypes:
		dt = row.get('dt')
		if row.get('issingle'):
			row['total'] = bool(frappe.db.exists(dt))
		else:
			row['total'] = frappe.db.count(dt)

	columns.append({"label": _("Total"), "fieldname": "total", "fieldtype": "Int"})

	return columns, doctypes
