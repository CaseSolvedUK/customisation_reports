// Copyright (c) 2022, CaseSolved and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["DocField Usage"] = {
	"filters": [
		{
			"fieldname":"app_name",
			"label": __("App Name"),
			"fieldtype": "Data",
		},
		{
			"fieldname":"module",
			"label": __("Module"),
			"fieldtype": "Link",
			"options": "Module Def"
		},
		{
			"fieldname":"issingle",
			"label": __("Is Single"),
			"fieldtype": "Select",
			"options": "\n0\n1"
		},
		{
			"fieldname":"name",
			"label": __("DocType"),
			"fieldtype": "Link",
			"options": "DocType"
		},
		{
			"fieldname":"fieldname",
			"label": __("DocField Name"),
			"fieldtype": "Data"
		},
		{
			"fieldname":"usage",
			"label": __("Usage % is less than"),
			"fieldtype": "Percent"
		},
		{
			"fieldname":"error",
			"label": __("SQL Error"),
			"fieldtype": "Data"
		},
	]
}
