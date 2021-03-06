// Copyright (c) 2022, CaseSolved and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Doctype Usage"] = {
	"filters": [
		{
			"fieldname":"app_name",
			"label": __("App Name"),
			"fieldtype": "Data"
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
			"fieldname":"total",
			"label": __("Total Rows"),
			"fieldtype": "Select",
			"options": "\n==0\n!=0"
		},
	]
}
