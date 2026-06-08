SELECT
    v.vendor_code AS "Vendor Code",
    v.vendor_name AS "Vendor Name",

    poi.sap_item_no AS "PO Line/Sap Item No",
    po.sap_code AS "Purchase Order No.",
    mt.name AS "Material Description",
    grn.reference AS "Bill No/reference",
    grn.bill_date AS "GRN's Invoice Dt",
    
    poi.quantity AS "Qty",
    grn.sap_code AS "GRN NO",
    poi.item_amount AS "Rate(Item Amount)",
    poi.rate AS "Rate(Rate Amount)",
    poi.taxable_amount AS "Taxable Amount",
    poi.cgst_amount AS "CGST Amount",
    poi.sgst_amount AS "SGST Amount",
    poi.igst_amount AS "IGST Amount",
    poi.total_amount AS "Total Amount",

    grn.total_amount AS "GRN Amount",
    sap_master.description AS "Purch. Grp. Desc.",

    v.gst_class AS "GST CLASS.",
    v.vendor_classif_text AS "Vendor Classif. text",

    grn.company_code AS "COMPANY Code(Grn)",
    co.sap_code AS "Company Sap Code",
    co.name AS "Company Name",
    co.gst_no AS "Company GSTIN",

    -- "Project tYPE" NA
    -- "Project Type desc" NA
    -- "Billing Element" NA
    -- "Nature of Goods" NA
    -- "Statiscal IO" NA
    -- "COMP STATE Name"
    v.region AS "Plant Region(Vendor)",
    -- "TCS" NA
    -- "Order Desc." NA
    -- "Cost Center Desc." NA
    -- "TDS" NA
    -- "Discount after tax" NA
    -- "Vendor IRN" NA
    -- "GRN IRN" NA
    

    v.gstin_status_category AS "gstin_status_category",
    -- "GSTIN Status Change Date" NA
    v.gstin_status AS "GSTIN Status(Vendor)",

    -- "Error Description 1" NA
    -- "Error Description 2" NA
    -- "1st Approver" NA
    -- "2nd Approver" NA
    -- "3rd Approver" NA

    -- ## Acc Assign GL  
    -- Acc Assign GL Name NA
    -- Account Assignment NA
    -- ## Amount excl tax 
    -- ## Amount with excise
    -- ## Asset

    -- CST 


    DATE(grn.created_at) AS "GRN Created Date(GRN Entry Date)",
    grn.batch AS "Batch No.(GRN)",
    grn.hsncode AS "Mat-HSN Code(Grn Hsn Code)",

    DATE(grn.date) AS "GRN Date",

    vm.sap_code AS item__sap_code,
    vm.material_code AS item__material_code,
    -- mt.name AS item__material_type__name,
    mtp.name AS item__material_type__parent__name,
    vm.material_name AS item__material_name,

    u.formal_name AS uom__formal_name,
    u.symbol AS uom__symbol,
    u.decimal_places AS uom__decimal_places,

    ind.request_code AS indent_item__indent__request_code,
    ind_item.approved_by_date AS indent_item__approved_by_date,

    q.request_code AS quotation_item__quotation__request_code,

    /* ✅ FIXED CST REQUEST CODE */
	(
		SELECT GROUP_CONCAT(DISTINCT CONCAT(c.request_code, ' V:', c.version))
		FROM procurement_cst_items ci
		JOIN procurement_cst c ON c.id = ci.cst_id
		WHERE ci.id = poi.cst_item_id
		AND c.latest = 1
		AND c.status NOT IN ('rejected','cancelled')
	) AS cst__request_code,

    po.request_code,
    po.version,
    po.date,
    po.delivery_days,
    po.scope_of_supply,
    ds.site_name AS delivery_site,
    bs.site_name AS billing_site,
    
    po.tax_type,
    po.status,
    

    -- procurement_grn_purchase_orders


    /* ✅ FIX grn_quantity */
    -- (
    --     SELECT SUM(gi.quantity)
    --     FROM procurement_grn_items gi
    --     JOIN procurement_grn g ON g.id = gi.grn_id
    --     WHERE g.is_deleted = 0
    --     AND gi.purchase_order_item_id = poi.id
    -- ) AS grn_quantity,

    /* ✅ GST */
    -- (poi.sgst_amount + poi.cgst_amount + poi.igst_amount + poi.utgst_amount) AS total_gst,

    /* ✅ Misc */
    (poi.excise_tax_amount + poi.cess_amount + poi.tax_amount) AS misc_charges,

    /* ✅ FIXED doc_list */
    (
        SELECT GROUP_CONCAT(DISTINCT CONCAT(pa.attachment_name, ':', pa.attachment))
        FROM procurement_purchase_order_attachments pa
        WHERE pa.purchase_order_id = poi.purchase_order_id
    ) AS doc_list,

    so.name,
    poi.status_of_order_id,
    poi.edd,
    poi.is_delivered,
    poi.tracker_code,
    poi.tracker_remarks,
    poi.id,

    poi.manual_received_quantity,
    poi.manual_return_quantity,
    poi.manual_quantity_remarks,
    poi.delivered_date,

    /* ✅ Real-time qty */
    IFNULL((
        SELECT SUM(rr.quantity)
        FROM procurement_real_time_material_receive rr
        WHERE rr.purchase_order_item_id = poi.id
    ), 0) AS real_time_received_quantity,

    /* ✅ BALANCE QUANTITY FIXED */s
    CASE
        WHEN IFNULL((
            SELECT SUM(gi.quantity)
            FROM procurement_grn_items gi
            WHERE gi.purchase_order_item_id = poi.id
        ), 0) >= IFNULL((
            SELECT SUM(rr.quantity)
            FROM procurement_real_time_material_receive rr
            WHERE rr.purchase_order_item_id = poi.id
        ), 0)
        THEN poi.quantity - IFNULL((
            SELECT SUM(gi.quantity)
            FROM procurement_grn_items gi
            WHERE gi.purchase_order_item_id = poi.id
        ), 0)
        ELSE poi.quantity - IFNULL((
            SELECT SUM(rr.quantity)
            FROM procurement_real_time_material_receive rr
            WHERE rr.purchase_order_item_id = poi.id
        ), 0)
    END AS balance_quantity,

    /* ✅ remarks */
    (
        SELECT r.remarks
        FROM procurement_material_request_item_remarks r
        WHERE r.material_request_item_id = poi.material_request_item_id
        AND r.remarks_type = 'general'
        ORDER BY r.created_at DESC
        LIMIT 1
    ) AS requisition_remarks,

    (
        SELECT r.remarks
        FROM procurement_material_request_item_remarks r
        WHERE r.material_request_item_id = poi.material_request_item_id
        AND r.remarks_type = 'purchase'
        ORDER BY r.created_at DESC
        LIMIT 1
    ) AS purchase_remarks

FROM procurement_purchase_order_items poi

LEFT JOIN procurement_purchase_order po ON po.id = poi.purchase_order_id
LEFT JOIN project_and_planning_projectmaster pr ON po.project_id = pr.id

LEFT JOIN vendor_vendormasterv2 v ON v.id = po.vendor_id
LEFT JOIN procurement_grn grn ON grn.purchase_order_id = po.id
LEFT JOIN procurement_sap_master sap_master ON po.purchase_group_for_sap = sap_master.id

LEFT JOIN material_master_vendormaterialmaster vm ON vm.id = poi.item_id
LEFT JOIN material_master_materialtype mt ON mt.id = vm.material_type_id
LEFT JOIN material_master_materialtype mtp ON mtp.id = mt.parent_id

LEFT JOIN material_master_unitofmesurement u ON u.id = poi.uom_id

LEFT JOIN procurement_indent_items ind_item ON ind_item.id = poi.indent_item_id
LEFT JOIN procurement_indent ind ON ind.id = ind_item.indent_id

LEFT JOIN procurement_rfq_quotation_items qi ON qi.id = poi.quotation_item_id
LEFT JOIN procurement_rfq_quotation q ON q.id = qi.quotation_id

LEFT JOIN procurement_site ds ON ds.id = po.delivery_site_id
LEFT JOIN procurement_site bs ON bs.id = po.billing_site_id

LEFT JOIN procurement_status_of_order so ON so.id = poi.status_of_order_id

LEFT JOIN administrations_company co ON co.id = pr.company_id

WHERE
    po.is_deleted = 0;