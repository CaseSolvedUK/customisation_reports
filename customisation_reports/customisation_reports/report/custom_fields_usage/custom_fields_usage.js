// Copyright (c) 2022, CaseSolved and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Custom Fields Usage"] = {
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
			"fieldtype": "Check"
		},
		{
			"fieldname":"dt",
			"label": __("Doctype"),
			"fieldtype": "Link",
			"options": "DocType"
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
