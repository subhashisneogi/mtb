SELECT DISTINCT
    gi.id,
    g.date                          AS grn__date,
    ps.sap_plant_id                 AS plant_code,
    pm.project_name                 AS plant_name,

    -- MR
    (
        SELECT GROUP_CONCAT(DISTINCT mr.request_code)
        FROM procurement_material_request_items mri
        INNER JOIN procurement_material_request mr ON mri.material_request_id = mr.id
        WHERE mri.id = gi.material_request_item_id
    ) AS material_request__request_code,

    (
        SELECT GROUP_CONCAT(DISTINCT DATE(mr.created_at))
        FROM procurement_material_request_items mri
        INNER JOIN procurement_material_request mr ON mri.material_request_id = mr.id
        WHERE mri.id = gi.material_request_item_id
    ) AS material_request__creation_date,

    (
        SELECT GROUP_CONCAT(DISTINCT DATE(mri.approved_by_date))
        FROM procurement_material_request_items mri
        WHERE mri.id = gi.material_request_item_id
    ) AS material_request__approved_by_date,

    -- Indent
    (
        SELECT GROUP_CONCAT(DISTINCT i.request_code)
        FROM procurement_indent_items ii
        INNER JOIN procurement_indent i ON ii.indent_id = i.id
        WHERE ii.id = gi.indent_item_id
    ) AS indent_request_code,

    (
        SELECT GROUP_CONCAT(DISTINCT DATE(i.created_at))
        FROM procurement_indent_items ii
        INNER JOIN procurement_indent i ON ii.indent_id = i.id
        WHERE ii.id = gi.indent_item_id
    ) AS indent_created_at,

    (
        SELECT GROUP_CONCAT(DISTINCT DATE(ii.approved_by_date))
        FROM procurement_indent_items ii
        WHERE ii.id = gi.indent_item_id
    ) AS indent_approved_by_date,

    g.movement_type                 AS mvt_type,
    g.sap_code                      AS mat_document,

    v.vendor_code                   AS vendor_sap_code,
    v.vendor_name                   AS vendor_name,
    m.sap_code                      AS material_code,
    m.material_name                 AS material_name,
    u.symbol                        AS uom,

    gi.received_quantity            AS received_quantity,
    gi.quantity                     AS ordered_quantity,
    gi.rate                         AS unit_rate,
    gi.item_amount                  AS item_amount,
    gi.taxable_amount               AS amt_in_local_curency,

    po.request_code                 AS purcahse_order,
    g.request_code                  AS grn__request_code,

    g.doc_header_text,
    g.header_text,

    m.material_code                 AS item__material_code,
    m.material_descriptions         AS item__material_descriptions,
    po.sap_code                     AS purchase_order_item__purchase_order__sap_code,
    s.site_name                     AS grn__site__site_name,
    m.sap_code                      AS item__sap_code,

    COALESCE((
        SELECT SUM(b.quantity)
        FROM procurement_grn_items_batch b
        WHERE b.grn_item_id = gi.id
    ), 0.0) AS total_batch_quantity,

    -- ================================================================
    -- total_budget_amount
    -- Chain: gi → poi → po → cst  gives us cst.rfq_vendor_id
    -- Then: QuotationItems where rfq_vendor_item.rfq_vendors_id = cst.rfq_vendor_id
    --       AND quotation.is_deleted=0, quotation.latest=1, is_selected_by_cst=1
    -- For each matching QuotationItem, get the latest budget rate from
    --   procurement_material_budget_breakdown → procurement_material_project
    --   matching (requested_material_id, project_id) with is_zero_budget=0
    -- total_budget_amount = SUM(budget_rate * quantity_by_cst)
    -- ================================================================
    COALESCE((
        SELECT SUM(
            COALESCE(
                (
                    SELECT pmbb.rate
                    FROM procurement_material_budget_breakdown pmbb
                    INNER JOIN procurement_material_project pmp
                        ON pmbb.master_id = pmp.id
                    WHERE pmp.requested_material_id = qi.requested_material_id
                      AND pmp.project_id            = q.project_id
                      AND pmbb.is_zero_budget        = 0
                      AND pmp.is_deleted             = 0
                    ORDER BY pmbb.entry_date DESC
                    LIMIT 1
                ),
                0.0
            ) * qi.quantity_by_cst
        )
        FROM procurement_rfq_quotation_items qi
        INNER JOIN procurement_rfq_quotation q
            ON qi.quotation_id = q.id
        INNER JOIN procurement_rfq_vendors_items rvi
            ON qi.rfq_vendor_item_id = rvi.id
        WHERE rvi.rfq_vendors_id   = cst.rfq_vendor_id
          AND q.is_deleted         = 0
          AND q.latest             = 1
          AND qi.is_selected_by_cst = 1
    ), 0.0) AS total_budget_amount

FROM procurement_grn_items gi

LEFT JOIN procurement_grn g
    ON gi.grn_id = g.id

LEFT JOIN procurement_store ps
    ON g.store_id = ps.id

LEFT JOIN vendor_vendormasterv2 v
    ON g.vendor_id = v.id

LEFT JOIN material_master_unitofmesurement u
    ON gi.uom_id = u.id

LEFT JOIN material_master_vendormaterialmaster m
    ON gi.item_id = m.id

LEFT JOIN procurement_purchase_order_items poi
    ON gi.purchase_order_item_id = poi.id

LEFT JOIN procurement_purchase_order po
    ON poi.purchase_order_id = po.id

-- CST join: provides rfq_vendor_id used by the budget subquery
LEFT JOIN procurement_cst cst
    ON po.cst_id = cst.id

LEFT JOIN project_and_planning_projectmaster pm
    ON po.project_id = pm.id

LEFT JOIN procurement_site s
    ON g.site_id = s.id

WHERE g.is_deleted = 0
  AND g.date >= '2026-04-01'
  AND g.date <  '2026-05-31';