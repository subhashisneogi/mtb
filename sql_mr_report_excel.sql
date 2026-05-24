SELECT
    mri.id AS `id`,
    mr.request_code AS `material_request__request_code`,
    mr.date AS `material_request__date`,
    mri.status AS `status`,

    mri.requested_material_id AS `requested_material`,
    vm.material_code AS `requested_material__material_code`,
    vm.sap_code AS `requested_material__sap_code`,
    vm.material_name AS `requested_material__material_name`,
    uom.symbol AS `requested_material__unit_of_mesurement__symbol`,
    mt.name AS `requested_material__material_type__name`,

    mri.approved_by_date AS `approved_by_date`,
    mri.quantity_unit AS `quantity_unit`,
    mri.sanctioned_quantity AS `sanctioned_quantity`,

    ii.id AS `procurement_material_indent_item_request`,
    rfqi.id AS `procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item`,
    csti.id AS `procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item`,
    poi.id AS `procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item`,
    grni.id AS `procurement_material_indent_item_request__procurement_rfq_vendors_item_indent_item__procurement_cst_item_rfq_vendor_item__procurement_purchase_order_item_cst_item__procurement_grn_item_purchase_order_item`,

    ind.request_code AS `indent__request_code`,
    ind.date AS `indent__date`,
    ind.status AS `indent__status`,
    COALESCE(ii.quantity, 0) AS `indent__quantity`,
    COALESCE(ii.sanctioned_quantity, 0) AS `indent__sanctioned_quantity`,
    ii.approved_by_date AS `indent__approved_by_date`,

    rfq.request_code AS `rfq_vendors__request_code`,
    rfq.date AS `rfq_vendors__date`,
    rfq.status AS `rfq_vendors__status`,

    COALESCE(quotation_data.quotation_count, 0) AS `quotation__count`,
    quotation_data.quotation_l_data AS `quotation__l_data`,

    cst.request_code AS `cst__request_code`,
    cst.version AS `cst__version`,
    cst.status AS `cst__status`,
    cst.current_stage AS `cst__current_stage`,
    cst.date AS `cst__date`,
    cst.total_item_item_quantity AS `cst__quantity`,

    po.request_code AS `purchase_order__request_code`,
    vendor.vendor_name AS `purchase_order__vendor__vendor_name`,
    po.date AS `purchase_order__date`,
    po.status AS `purchase_order__status`,
    COALESCE(poi.quantity, 0) AS `purchase_order__quantity`,
    COALESCE(poi.rate, 0) AS `purchase_order__rate`,
    COALESCE(poi.total_amount, 0) AS `purchase_order__total_amount`,
    COALESCE(poi.tax_amount, 0) AS `purchase_order__tax_amount`,
    po.approved_by_date AS `purchase_order__approved_by_date`,
    po.sap_code AS `purchase_order__sap_code`,
    po.final_release_date_from_sap AS `purchase_order__final_release_date_from_sap`,

    COALESCE(SUM(grni.quantity), 0) AS `grn__received_quantity`,

    GROUP_CONCAT(DISTINCT bpr.balance_po_remarks SEPARATOR ', ') AS `balance_po_remarks`,

    COALESCE((
        SELECT SUM(poe.total_expense_amount)
        FROM procurement_purchase_order_expense poe
        INNER JOIN misc_expense_head eh
            ON eh.id = poe.expense_head_id
        WHERE poe.purchase_order_id = po.id
          AND eh.name = 'Freight'
          AND poe.is_deleted = 0
    ), 0) AS `purchase_order__freight`

FROM procurement_material_request_items mri

LEFT JOIN procurement_material_request mr
    ON mr.id = mri.material_request_id

LEFT JOIN material_master_vendormaterialmaster vm
    ON vm.id = mri.requested_material_id

LEFT JOIN material_master_unitofmesurement uom
    ON uom.id = vm.unit_of_mesurement_id

LEFT JOIN material_master_materialtype mt
    ON mt.id = vm.material_type_id

LEFT JOIN procurement_indent_items ii
    ON ii.material_request_item_id = mri.id
   AND ii.is_deleted = 0

LEFT JOIN procurement_indent ind
    ON ind.id = ii.indent_id
   AND ind.is_deleted = 0

LEFT JOIN procurement_rfq_vendors_items rfqi
    ON rfqi.indent_item_id = ii.id
   AND rfqi.is_deleted = 0

LEFT JOIN procurement_rfqvendors rfq
    ON rfq.id = rfqi.rfq_vendors_id
   AND rfq.is_deleted = 0

LEFT JOIN (
    SELECT
        ranked_q.rfq_vendor_id,

        COUNT(ranked_q.id) AS quotation_count,

        GROUP_CONCAT(
            CONCAT(
                ranked_q.l_status,
                ' | SAP CODE: ', IFNULL(ranked_q.vendor_code, ''),
                ' | Vendor Name: ', IFNULL(ranked_q.vendor_name, ''),
                ' | Vendor Address: ', IFNULL(ranked_q.vendor_address, ''),
                ' | Quotation No: ', IFNULL(ranked_q.request_code, ''),
                ' | Quotation Date: ', IFNULL(DATE(ranked_q.created_at), ''),
                ' | CST Qty: ', IFNULL(ranked_q.cst_qty, 0),
                ' | Basic Rate: ', IFNULL(ranked_q.total_item_item_amount, 0),
                ' | Freight: ', IFNULL(ranked_q.total_expense_expense_amount, 0),
                ' | Tax: ', IFNULL(ranked_q.total_tax_total_tax_amount, 0),
                ' | Amount: ', IFNULL(ranked_q.total_amount, 0)
            )
            ORDER BY ranked_q.l_rank ASC
            SEPARATOR ' || '
        ) AS quotation_l_data

    FROM (
        SELECT
            q.id,
            q.rfq_vendor_id,
            q.request_code,
            q.created_at,
            q.total_item_item_amount,
            q.total_expense_expense_amount,
            q.total_tax_total_tax_amount,
            q.total_amount,

            v.vendor_code,
            v.vendor_name,
            v.vendor_address,

            latest_cst.total_item_item_quantity AS cst_qty,

            DENSE_RANK() OVER (
                PARTITION BY q.rfq_vendor_id
                ORDER BY q.total_amount ASC
            ) AS l_rank,

            CONCAT(
                'L',
                DENSE_RANK() OVER (
                    PARTITION BY q.rfq_vendor_id
                    ORDER BY q.total_amount ASC
                )
            ) AS l_status

        FROM procurement_rfq_quotation q

        LEFT JOIN vendor_vendormasterv2 v
            ON v.id = q.vendor_id

        LEFT JOIN (
            SELECT
                c1.rfq_vendor_id,
                c1.total_item_item_quantity
            FROM procurement_cst c1
            INNER JOIN (
                SELECT
                    rfq_vendor_id,
                    MAX(version) AS max_version
                FROM procurement_cst
                WHERE is_deleted = 0
                  AND latest = 1
                GROUP BY rfq_vendor_id
            ) c2
                ON c2.rfq_vendor_id = c1.rfq_vendor_id
               AND c2.max_version = c1.version
            WHERE c1.is_deleted = 0
              AND c1.latest = 1
        ) latest_cst
            ON latest_cst.rfq_vendor_id = q.rfq_vendor_id

        WHERE q.is_deleted = 0
          AND q.latest = 1
    ) ranked_q

    GROUP BY ranked_q.rfq_vendor_id
) quotation_data
    ON quotation_data.rfq_vendor_id = rfq.id

LEFT JOIN procurement_cst_items csti
    ON csti.rfq_vendor_item_id = rfqi.id
   AND csti.is_deleted = 0

LEFT JOIN procurement_cst cst
    ON cst.id = csti.cst_id
   AND cst.is_deleted = 0

LEFT JOIN procurement_purchase_order_items poi
    ON poi.cst_item_id = csti.id
   AND poi.is_deleted = 0

LEFT JOIN procurement_purchase_order po
    ON po.id = poi.purchase_order_id
   AND po.is_deleted = 0

LEFT JOIN procurement_grn_items grni
    ON grni.purchase_order_item_id = poi.id
   AND grni.is_deleted = 0

LEFT JOIN procurement_balance_po_remarks bpr
    ON (
        bpr.material_request_item_id = mri.id
        OR bpr.indent_item_id = ii.id
        OR bpr.rfq_vendor_item_id = rfqi.id
        OR bpr.cst_item_id = csti.id
        OR bpr.purchase_order_item_id = poi.id
    )
   AND bpr.is_deleted = 0

LEFT JOIN vendor_vendormasterv2 vendor
    ON vendor.id = po.vendor_id

WHERE mri.is_deleted = 0

GROUP BY
    mri.id,
    mr.request_code,
    mr.date,
    mri.status,
    mri.requested_material_id,
    vm.material_code,
    vm.sap_code,
    vm.material_name,
    uom.symbol,
    mt.name,
    mri.approved_by_date,
    mri.quantity_unit,
    mri.sanctioned_quantity,
    ii.id,
    rfqi.id,
    csti.id,
    poi.id,
    grni.id,
    ind.request_code,
    ind.date,
    ind.status,
    ii.quantity,
    ii.sanctioned_quantity,
    ii.approved_by_date,
    rfq.request_code,
    rfq.date,
    rfq.status,
    quotation_data.quotation_count,
    quotation_data.quotation_l_data,
    cst.request_code,
    cst.version,
    cst.status,
    cst.current_stage,
    cst.date,
    cst.total_item_item_quantity,
    po.request_code,
    vendor.vendor_name,
    po.date,
    po.status,
    poi.quantity,
    poi.rate,
    poi.total_amount,
    poi.tax_amount,
    po.approved_by_date,
    po.sap_code,
    po.final_release_date_from_sap

ORDER BY mri.id DESC;