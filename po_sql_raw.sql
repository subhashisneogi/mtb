SELECT
    po.id,
    
    -- po_doc_list: concatenated attachments
    (
        SELECT GROUP_CONCAT(DISTINCT CONCAT(poa.attachment_name, ':', poa.attachment))
        FROM procurement_purchase_order_attachments poa
        WHERE poa.purchase_order_id = po.id
          AND poa.is_deleted = 0
    ) AS po_doc_list,

    bs.site_name AS billing_site__site_name,
    ds.site_name AS delivery_site__site_name,

    -- grn_quantity
    COALESCE((
        SELECT SUM(gi.quantity)
        FROM procurement_grn_items gi
        JOIN procurement_grn g ON g.id = gi.grn_id
        WHERE gi.grn_id = g.id
          AND g.is_deleted = 0
          AND gi.is_deleted = 0
          AND gi.purchase_order_item_id IN (
              SELECT poi.id FROM procurement_purchase_order_items poi
              WHERE poi.purchase_order_id = po.id AND poi.is_deleted = 0
          )
          AND g.status NOT IN ('rejected', 'cancelled')
    ), 0) AS grn_quantity,

    -- grn_amount
    COALESCE((
        SELECT SUM(gi.item_amount)
        FROM procurement_grn_items gi
        JOIN procurement_grn g ON g.id = gi.grn_id
        WHERE g.is_deleted = 0
          AND gi.is_deleted = 0
          AND gi.purchase_order_item_id IN (
              SELECT poi.id FROM procurement_purchase_order_items poi
              WHERE poi.purchase_order_id = po.id AND poi.is_deleted = 0
          )
          AND g.status NOT IN ('rejected', 'cancelled')
    ), 0) AS grn_amount,

    js.site_name AS job_site__site_name,

    -- indent__request_code
    (
        SELECT GROUP_CONCAT(DISTINCT i.request_code)
        FROM procurement_indent i
        JOIN procurement_indent_items ii   ON ii.indent_id = i.id
        JOIN procurement_purchase_order_items poi ON poi.id = ii.id  -- indent_item FK
        WHERE poi.purchase_order_id = po.id
          AND i.is_deleted = 0
          AND ii.is_deleted = 0
          AND i.status NOT IN ('rejected', 'cancelled')
    ) AS indent__request_code,

    -- indent__date
    (
        SELECT GROUP_CONCAT(DISTINCT i.date)
        FROM procurement_indent i
        JOIN procurement_indent_items ii ON ii.indent_id = i.id
        JOIN procurement_purchase_order_items poi ON poi.indent_item_id = ii.id
        WHERE poi.purchase_order_id = po.id
          AND i.is_deleted = 0
          AND ii.is_deleted = 0
          AND i.status NOT IN ('rejected', 'cancelled')
    ) AS indent__date,

    po.request_code,
    po.version,
    po.date,
    po.delivery_days,

    -- quotation__request_code
    (
        SELECT GROUP_CONCAT(DISTINCT q.request_code)
        FROM procurement_rfq_quotation q
        JOIN procurement_rfq_quotation_items qi ON qi.quotation_id = q.id
        JOIN procurement_purchase_order_items poi ON poi.quotation_item_id = qi.id
        WHERE poi.purchase_order_id = po.id
          AND q.is_deleted = 0
          AND qi.is_deleted = 0
          AND q.status NOT IN ('rejected', 'cancelled')
    ) AS quotation__request_code,

    -- quotation__date
    (
        SELECT GROUP_CONCAT(DISTINCT q.date)
        FROM procurement_rfq_quotation q
        JOIN procurement_rfq_quotation_items qi ON qi.quotation_id = q.id
        JOIN procurement_purchase_order_items poi ON poi.quotation_item_id = qi.id
        WHERE poi.purchase_order_id = po.id
          AND q.is_deleted = 0
          AND qi.is_deleted = 0
          AND q.status NOT IN ('rejected', 'cancelled')
    ) AS quotation__date,

    v.vendor_name   AS vendor__vendor_name,
    po.vendor_id,
    v.vendor_code   AS vendor__vendor_code,

    -- cst__request_code
    (
        SELECT GROUP_CONCAT(DISTINCT CONCAT(c.request_code, ' V:', c.version))
        FROM procurement_cst c
        JOIN procurement_cst_items ci ON ci.cst_id = c.id
        JOIN procurement_purchase_order_items poi ON poi.cst_item_id = ci.id
        WHERE poi.purchase_order_id = po.id
          AND c.is_deleted = 0
          AND ci.is_deleted = 0
          AND c.latest = 1
          AND c.status NOT IN ('rejected', 'cancelled')
    ) AS cst__request_code,

    -- cst__id
    (
        SELECT GROUP_CONCAT(DISTINCT c.id)
        FROM procurement_cst c
        JOIN procurement_cst_items ci ON ci.cst_id = c.id
        JOIN procurement_purchase_order_items poi ON poi.cst_item_id = ci.id
        WHERE poi.purchase_order_id = po.id
          AND c.is_deleted = 0
          AND ci.is_deleted = 0
          AND c.latest = 1
          AND c.status NOT IN ('rejected', 'cancelled')
    ) AS cst__id,

    po.status,
    po.total_item_item_quantity,
    po.total_item_item_amount,
    po.total_item_disc_amount,
    po.tax_type,
    po.total_item_sgst_amount,
    po.total_item_igst_amount,
    po.total_item_cgst_amount,
    po.total_item_utgst_amount,
    po.total_expense_total_expense_amount,
    po.total_tax_total_tax_amount,
    po.total_amount,
    po.scope_of_supply,
    po.sap_code,
    po.project_id,
    po.site_id,
    s.site_name     AS site__site_name,
    po.store_id,

    -- pm__total__amount
    COALESCE((
        SELECT SUM(pm.amount)
        FROM procurement_payment_master pm
        WHERE pm.purchase_order_id = po.id
          AND pm.is_deleted = 0
          AND pm.status NOT IN ('rejected', 'cancelled')
    ), 0) AS pm__total__amount,

    -- pm__processed__amount
    COALESCE((
        SELECT SUM(utr.amount)
        FROM procurement_payment_master_utr utr
        JOIN procurement_payment_master pm ON pm.id = utr.payment_master_id
        WHERE pm.purchase_order_id = po.id
          AND pm.is_deleted = 0
          AND utr.is_deleted = 0
          AND pm.status NOT IN ('rejected', 'cancelled')
    ), 0) AS pm__processed__amount,

    -- pm__under_processed__amount
    COALESCE(
        COALESCE((
            SELECT SUM(pm.amount)
            FROM procurement_payment_master pm
            WHERE pm.purchase_order_id = po.id
              AND pm.is_deleted = 0
              AND pm.status NOT IN ('rejected', 'cancelled')
        ), 0)
        -
        COALESCE((
            SELECT SUM(utr.amount)
            FROM procurement_payment_master_utr utr
            JOIN procurement_payment_master pm ON pm.id = utr.payment_master_id
            WHERE pm.purchase_order_id = po.id
              AND pm.is_deleted = 0
              AND utr.is_deleted = 0
              AND pm.status NOT IN ('rejected', 'cancelled')
        ), 0)
    , 0) AS pm__under_processed__amount,

    proj.project_name           AS project__project_name,
    proj.project_code           AS project__project_code,
    proj.project_classification AS project__project_classification,
    proj.attachment             AS project__attachment
    -- comp.name                   AS project__project_company_name

FROM procurement_purchase_order po

-- joins for select_related fields
LEFT JOIN procurement_site       bs   ON bs.id   = po.billing_site_id
LEFT JOIN procurement_site       ds   ON ds.id   = po.delivery_site_id
LEFT JOIN procurement_site       js   ON js.id   = po.job_site_id
LEFT JOIN procurement_site       s    ON s.id    = po.site_id
LEFT JOIN vendor_vendormasterv2  v    ON v.id    = po.vendor_id
LEFT JOIN project_and_planning_projectmaster proj ON proj.id = po.project_id
-- LEFT JOIN administrations_company comp ON comp.id = proj.company_id 

WHERE
    po.is_deleted = 0;
    -- AND <your dynamic search filters go here>

-- ORDER BY
--     po.request_code;