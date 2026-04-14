const baseFlags = {
    status: "5 stars",
    is_active: 1,
    is_locked: 0,
    is_deleted: 0,  // 1-deleted. 0-default. 2.TBD/hidden, always show 0. never show 2.
    created_at: new Date(),
    updated_at: new Date(),
};



// Master seed data for new business entities
export const seed_data = {

    user_profile: (uid: string) => ({
        u_type: "free202509", // standard | admin
        u_logo: "",
        u_reward_balance: 800,
        u_locale: "en-US",
        u_referral_code: uid.slice(0, 6),
        u_referred_by: "aiautoinvoicing@gmail.com", // email
        u_plan: {
            type: "Gold",           // free, pro, etc.
            start: new Date(),       // plan or trial start date
            expires: new Date(new Date().setMonth(new Date().getMonth() + 3)), // 3 months trial
            isActive: true,          // indicates if trial/plan is currently active
        },
        u_referrals: [        // track each person this user referred
            {
                ref_uid: "referredUserUid",
                ref_email: "aiautoinvoicing@gmail.com",
                ref_created_at: new Date(),
                ref_reward_term: "trial_extension_1month", // type of reward
            }
        ],
        ...baseFlags,
    }),

    business_entity: {
        user_id: "user_id_aiautoinvoicing",

        be_id: "be_id_aiautoinvoicing",  // when creating new biz, replace with uuid
        be_logo: "",
        be_name: "My Corporation",
        be_address: "1600 Pennsylvania Ave.,\nWashington DC",
        be_contact: "John Doe",
        be_contact_title: "CEO",
        be_email: "change@me.com",
        be_phone: "1-888-168-5868",
        be_website: "https://aiautoinvoicing.github.io",
        be_type: "sole_proprietorship",

        be_biz_number: "87-3322034",
        be_tax_id: "085868671",
        be_bank_info: "Bank Name: TD Bank\nAccount Number: 8683451796\nRouting Number: 021000021",
        be_payment_term: 7,

        be_currency: "USD",
        be_inv_template_id: "t1",
        be_description: "This is a note for the bissiness.",
        be_note: "This is a note for the bissiness.",

        be_timezone: "America/New_York",
        be_date_format: "MM/DD/YYYY",

        be_inv_prefix: "INV-",
        be_inv_integer: 2501,
        be_inv_integer_max: 2501,
        be_show_paid_stamp: true, // Show "Paid" stamp on invoices by default

        be_plan_id: "plan25_1",
        be_plan_name: "Free Forever",
        be_plan251_expired: new Date(new Date().setDate(new Date().getDate() + 101)), // 3 months free trial
        be_plan252_expired: new Date(new Date().setDate(new Date().getDate() - 1)),
        be_plan253_expired: new Date(new Date().setDate(new Date().getDate() - 2)),
        be_plan254_expired: new Date(new Date().setDate(new Date().getDate() - 3)),
        be_plan255_expired: new Date(new Date().setDate(new Date().getDate() - 4)),
        be_plan256_expired: new Date(new Date().setDate(new Date().getDate() - 5)),
        be_plan257_expired: new Date(new Date().setDate(new Date().getDate() - 6)),
        be_plan258_expired: new Date(new Date().setDate(new Date().getDate() - 7)),
        be_plan259_expired: new Date(new Date().setDate(new Date().getDate() - 8)),

        ...baseFlags,
    },

    other_charges: [
        {
            fee_id: "fee_000",
            fee_name: "Other Charges",
            fee_amount: 0,
            fee_note: "Detailed description of other charges should be put into invoice notes.",
            ...baseFlags,
        },
        {
            fee_id: "fee_shipping",
            fee_name: "Shipping",
            fee_amount: 10,
            fee_note: "Shipping charges.",
            ...baseFlags,
        },
        {
            fee_id: "fee_handling",
            fee_name: "Handling",
            fee_amount: 100,
            fee_note: "Costs related to packaging, handling, or special processing.",
            ...baseFlags,
        },
        {
            fee_id: "fee_late_fee",
            fee_name: "Late Fee",
            fee_amount: 1,
            fee_note: "Fee applied for overdue invoices or delayed payment.",
            ...baseFlags,
        },
        {
            fee_id: "fee_insurance",
            fee_name: "Insurance",
            fee_amount: 1,
            fee_note: "Optional insurance for shipping or service coverage.",
            ...baseFlags,
        },
        {
            fee_id: "fee_service_fee",
            fee_name: "Service Fee",
            fee_amount: 10,
            fee_note: "Charges for extra services provided.",
            ...baseFlags,
        },
        {
            fee_id: "fee_miscellaneous",
            fee_name: "Miscellaneous",
            fee_amount: 1,
            fee_note: "Other minor charges not included in other categories.",
            ...baseFlags,
        },
    ],

    // Payment methods seed data
    payment_methods: [
        {
            pm_id: "pm_deposit",
            pm_name: "Deposit",
            pm_note: "Deposit.",
            ...baseFlags,
        },
        {
            pm_id: "pm_credit_card",
            pm_name: "Credit Card",
            pm_note: "Processed via Stripe, Square, Paypal, or similar payment processors.",
            ...baseFlags,
        },
        {
            pm_id: "pm_check",
            pm_name: "Check",
            pm_note: "Make payable to your business name as shown on the invoice.",
            ...baseFlags,
        },
        {
            pm_id: "pm_cash",
            pm_name: "Cash",
            pm_note: "Accepted for in-person/local transactions only.",
            ...baseFlags,
        },
        {
            pm_id: "pm_bank_transfer_ach",
            pm_name: "Bank Transfer (ACH)",
            pm_note: "U.S. bank transfer. Routing and account number required.",
            ...baseFlags,
        },
        {
            pm_id: "pm_wire_transfer",
            pm_name: "Wire Transfer",
            pm_note: "International or domestic wire transfer. Bank fees may apply.",
            ...baseFlags,
        },
        {
            pm_id: "pm_paypal",
            pm_name: "PayPal",
            pm_note: "Send payments to your PayPal email address (e.g., user@example.com).",
            ...baseFlags,
        },
        {
            pm_id: "pm_bank_transfer_eft",
            pm_name: "Bank Transfer (EFT)",
            pm_note: "Electronic Funds Transfer (EFT) for Canadian customers.",
            ...baseFlags,
        },
        {
            pm_id: "pm_interac_e_transfer",
            pm_name: "Interac e-Transfer",
            pm_note: "Available for Canadian bank customers only.",
            ...baseFlags,
        },
        {
            pm_id: "pm_z_other",
            pm_name: "Other",
            pm_note: "Refer to the invoice note for custom payment instructions.",
            ...baseFlags,
        },
    ],

    tax_list: [
        // Canada
        {
            tax_id: "tax_hst",
            tax_name: "HST",
            tax_rate: 13,
            tax_type: "federal",
            tax_note: "Canada Harmonized Sales Tax",

            ...baseFlags,
        },
        {
            tax_id: "tax_gst",
            tax_name: "GST",
            tax_rate: 5,
            tax_type: "federal",
            tax_note: "Canada Goods & Services Tax",
            ...baseFlags,
        },
        {
            tax_id: "tax_pst",
            tax_name: "PST",
            tax_rate: 7,
            tax_type: "provincial",
            tax_note: "Provincial Sales Tax (e.g. BC)",
            ...baseFlags,
        },
        {
            tax_id: "tax_qst",
            tax_name: "QST",
            tax_rate: 9.975,
            tax_type: "provincial",
            tax_note: "Quebec Sales Tax",
            ...baseFlags,
        },

        // United States
        {
            tax_id: "sales_tax1",
            tax_name: "Sales Tax",
            tax_rate: 8.875,
            tax_type: "state",
            tax_note: "NY",
            ...baseFlags,
        },
        {
            tax_id: "sales_tax2",
            tax_name: "Sales Tax",
            tax_rate: 7.25,
            tax_type: "county",
            tax_note: "CA",
            ...baseFlags,
        },
        {
            tax_id: "sales_tax4",
            tax_name: "Sales Tax",
            tax_rate: 9.5,
            tax_type: "district",
            tax_note: "LA Chicago Seattle",
            ...baseFlags,
        },
    ],


    clients: [
        {
            client_id: "Client_TBD",
            client_number: "Client_TBD",
            client_company_name: "Client_TBD",
            client_contact_name: "Client_TBD",
            client_contact_title: "Client_TBD",
            client_business_number: "Client_TBD",
            client_tax_id: "Client_TBD",
            client_address: "Client_TBD",
            client_email: "TBD@example.com",
            client_mainphone: "555-567-8901",
            client_secondphone: "Client_TBD",
            client_fax: "Client_TBD",
            client_website: "Client_TBD",
            client_currency: "OTHER",
            client_template_id: "t1",

            client_status: "active",
            client_note: "Requires itemized invoices",

            client_payment_method: "Bank Transfer",
            client_payment_term: 15,
            client_terms_conditions: "Payment due in 7 days.",
            ...baseFlags,
            is_deleted: 2, //hidden
        },

        {
            client_id: "c_demo_1",          // 1    
            client_number: "c_demo_1",   // 2 Unique client number/code     
            client_business_number: "123456RT001",  // 3 Business registration number

            client_company_name: "Sterling Group (Demo)",   // 4
            client_contact_name: "Rebecca Hughes",   // 5
            client_contact_title: "Manager",    // 6
            client_address: "101 Market Street, San Francisco, CA 94105",            // 7
            client_email: "rebecca.hughes@sterling.ai",  // 8
            client_mainphone: "555-123-4567",   // 9
            client_secondphone: "second phone", // 10
            client_fax: "fax",      // 11
            client_website: "https://SterlingAdv.ai",  // 12


            client_currency: "USD",   // 13
            client_tax_id: "123456RT001",   // 14 Tax identification number
            client_payment_term: 15,    // 15 Payment term in days
            client_payment_method: "Bank Transfer", // 16   Payment method

            client_template_id: "t1",   // 17
            client_terms_conditions: "Payment due in 7 days.",   // 18  
            client_note: "Preferred contact time: Morning",  // 19

            ...baseFlags,
        },
        {
            client_id: "c_demo_2",          // 1    
            client_number: "c_demo_2",   // 2 Unique client number/code     
            client_business_number: "868-581-001",  // 3 Business registration number

            client_company_name: "Summit Tech Partners (Demo)",   // 4
            client_contact_name: "Jason Liu",   // 5
            client_contact_title: "Director",    // 6
            client_address: "202 Innovation Way, Austin, TX 78701",            // 7
            client_email: "jason.liu@summittech.com",  // 8
            client_mainphone: "555-987-6543",   // 9
            client_secondphone: "second phone", // 10
            client_fax: "fax",      // 11
            client_website: "https://summittech.com",  // 12
            client_currency: "USD",   // 13
            client_tax_id: "123456RT001",   // 14 Tax identification number
            client_payment_term: 30,    // 15 Payment term in days
            client_payment_method: "Bank Transfer", // 16   Payment method  

            client_template_id: "t1",   // 17
            client_terms_conditions: "Payment due in 7 days.",   // 18      
            client_note: "Send invoice by email only",  // 19

            ...baseFlags
        },
        {
            client_id: "c_demo_3",          // 1    
            client_number: "c_demo_3",   // 2 Unique client number/code     
            client_business_number: "868-588-001",  // 3 Business registration number

            client_company_name: "VitalCare Medical Center (Demo)",    // 4
            client_contact_name: "Emily Davis",   // 5
            client_contact_title: "Procurement Officer",    // 6
            client_address: "303 Health Blvd, Miami, FL 33101",            // 7
            client_email: "emily.davis@vitalcare.com",  // 8
            client_mainphone: "555-678-9012",   // 9
            client_secondphone: "second phone", // 10
            client_fax: "fax",      // 11
            client_website: "https://vitalcare.com",  // 12
            client_currency: "USD",   // 13
            client_tax_id: "123456RT001",   // 14 Tax identification number
            client_payment_term: 30,    // 15 Payment term in days
            client_payment_method: "Bank Transfer", // 16   Payment method

            client_template_id: "t1",   // 17
            client_terms_conditions: "Payment due in 7 days.",   // 18      
            client_note: "Send invoice by email only",  // 19

            ...baseFlags
        },
    ],


    // Payment methods seed data
    items: [
        {
            item_id: "Item_TBD",
            item_number: 'Item_TBD',
            item_name: "🚧Item_TBD",
            item_rate: 1.00,
            item_unit: 'Item_TBD',
            item_sku: "Item_TBD",
            item_description: "Item_TBD",

            item_quantity: 1,  // for InvItem only
            item_note: "For InvItem Only",      // for InvItem only
            item_amount: 1,    // for InvItem only

            ...baseFlags,
            is_deleted: 2, //TBD Item
        },
        {
            item_id: "T000",
            item_number: 'P002',
            item_name: "Adjustment",
            item_rate: 1.00,
            item_unit: "item",
            item_sku: "SKU 4225-776-3234",
            item_description: "additional charges or credits",

            item_quantity: 1,  // for InvItem only
            item_note: "For InvItem Only",      // for InvItem only
            item_amount: 2,    // for InvItem only
            ...baseFlags,
        },
        {
            item_id: "T120",
            item_number: 'P003',
            item_name: "Product ",
            item_rate: 1500.00,
            item_unit: "project",
            item_sku: "6IN-RD-CM-CO",
            item_description: "Tangible goods or materials delivered",

            item_quantity: 1,  // for InvItem only
            item_note: "For InvItem Only",      // for InvItem only
            item_amount: 1500,    // for InvItem only
            ...baseFlags,
        },
        {
            item_id: "T130",
            item_number: 'P0031',
            item_name: "Consulting Session",
            item_rate: 100.00,
            item_unit: "hour",
            item_sku: "SH123-BLK-8",
            item_description: "Business strategy session (1hr)",

            item_quantity: 1,  // for InvItem only
            item_note: "For InvItem Only",      // for InvItem only
            item_amount: 120,    // for InvItem only
            ...baseFlags,
        },
    ],


    invs: [
        {
            inv_id: "i_1001",
            user_id: 1,
            be_id: 1,

            client_id: "c_demo_3",          // 1    
            client_number: "c_demo_3",   // 2 Unique client number/code     
            client_business_number: "868-588-001",  // 3 Business registration number

            client_company_name: "VitalCare Medical Center (Demo)",    // 4
            client_contact_name: "Emily Davis",   // 5
            client_contact_title: "Procurement Officer",    // 6
            client_address: "303 Health Blvd, Miami, FL 33101",            // 7
            client_email: "emily.davis@vitalcare.com",  // 8
            client_mainphone: "555-678-9012",   // 9
            client_secondphone: "second phone", // 10
            client_fax: "fax",      // 11
            client_website: "https://vitalcare.com",  // 12
            client_currency: "USD",   // 13
            client_tax_id: "123456RT001",   // 14 Tax identification number
            client_payment_term: 30,    // 15 Payment term in days
            client_payment_method: "Bank Transfer", // 16   Payment method

            client_template_id: "t1",   // 17
            client_terms_conditions: "Payment due in 7 days.",   // 18      
            client_note: "Send invoice by email only",  // 19


            inv_number: "INV-1001",
            inv_date: new Date(),
            inv_due_date: new Date(),

            inv_title: "Invoice for Demo Client 1",
            inv_payment_requirement: "Net 7 days",
            inv_payment_term: 7,
            inv_reference: "PO#-001",
            inv_currency: "USD",

            inv_subtotal: 240.00,
            inv_discount: 0.0,
            inv_tax_label: "Tax",
            inv_tax_rate: 0.0,
            inv_tax_amount: 0.0,
            inv_shipping: 0.0,
            inv_handling: 0.0,
            inv_deposit: 0.0,
            inv_adjustment: 0.0,
            inv_other_charges_label: "Other Charges",
            inv_other_charges_amount: 0.0,
            inv_total: 240.00,

            inv_paid_total: 0.0,
            inv_balance_due: 240.00,
            inv_payment_status: "Unpaid",

            inv_flag_word: "Unpaid",
            inv_flag_emoji: "🟡",

            inv_pdf_template: "default",
            inv_notes: "Thank you for your business!",
            inv_terms_conditions: "Thank you for your business!",

            inv_items: [
                {
                    item_id: "T130",
                    item_number: "T130",
                    item_name: "Consulting Session",
                    item_description: "Business strategy session (1hr)",
                    item_sku: "SH123-BLK-8",
                    item_rate: 120.00,
                    item_unit: "hour",
                    item_note: "notes",
                    item_quantity: 2,
                    item_amount: 240.00,
                },
                {
                    item_id: "T131",
                    item_number: "T131",
                    item_name: "AI Service",
                    item_description: "AI-driven business strategy session (1hr)",
                    item_sku: "SH123-BLK-9",
                    item_rate: 1110.00,
                    item_unit: "hour",
                    item_note: "notes",
                    item_quantity: 2,
                    item_amount: 2220.00,
                },
            ],
            inv_payments: [],
            ...baseFlags,
        },
        {
            inv_id: "i_1002",
            user_id: 1,
            be_id: 1,
            client_id: "c_demo_2",          // 1    
            client_number: "c_demo_2",   // 2 Unique client number/code     
            client_business_number: "868-581-001",  // 3 Business registration number

            client_company_name: "Summit Tech Partners (Demo)",   // 4
            client_contact_name: "Jason Liu",   // 5
            client_contact_title: "Director",    // 6
            client_address: "202 Innovation Way, Austin, TX 78701",            // 7
            client_email: "jason.liu@summittech.com",  // 8
            client_mainphone: "555-987-6543",   // 9
            client_secondphone: "second phone", // 10
            client_fax: "fax",      // 11
            client_website: "https://summittech.com",  // 12
            client_currency: "USD",   // 13
            client_tax_id: "123456RT001",   // 14 Tax identification number
            client_payment_term: 30,    // 15 Payment term in days
            client_payment_method: "Bank Transfer", // 16   Payment method  

            client_template_id: "t1",   // 17
            client_terms_conditions: "Payment due in 7 days.",   // 18      
            client_note: "Send invoice by email only",  // 19


            inv_number: "INV-1002",
            inv_title: "Invoice for Demo Client 2",
            inv_date: new Date(),
            inv_due_date: new Date(),
            inv_payment_requirement: "Net 10 days",
            inv_payment_term: 10,
            inv_reference: "PO#-002",
            inv_currency: "CAD",

            inv_subtotal: 1500.00,
            inv_discount: 0.0,
            inv_tax_label: "Tax",
            inv_tax_rate: 0.13,
            inv_tax_amount: 195.00,
            inv_shipping: 0.0,
            inv_handling: 0.0,
            inv_deposit: 0.0,
            inv_adjustment: 0.0,
            inv_other_charges_label: "Other Charges",
            inv_other_charges_amount: 0.0,
            inv_total: 1695.00,

            inv_paid_total: 1695.00,
            inv_balance_due: 0.00,
            inv_payment_status: "Paid",

            inv_flag_word: "Paid",
            inv_flag_emoji: "🟢",

            inv_pdf_template: "default",
            inv_notes: "Thank you for your business!",
            inv_terms_conditions: "Thank you for your business!",

            inv_items: [
                {
                    item_id: "T120",
                    item_number: "T120",
                    item_name: "Product ",
                    item_description: "Tangible goods or materials delivered",
                    item_sku: "6IN-RD-CM-CO",
                    item_rate: 1500.00,
                    item_unit: "project",
                    item_note: "Notes.",
                    item_quantity: 1,
                    item_amount: 1500.00,
                },
            ],
            inv_payments: [
                {
                    pm_id: "pm_1001",
                    pm_name: "Bank Transfer",
                    pm_note: "Payment for invoice INV-1002",

                    pay_date: new Date(),
                    pay_amount: 1695.00,
                    pay_reference: "TRX001",
                    pay_note: "Paid in full",
                },
            ],
            ...baseFlags,
        },
        {
            inv_id: "i_1003",
            user_id: 1,
            be_id: 1,
            client_id: "c_demo_1",          // 1    
            client_number: "c_demo_1",   // 2 Unique client number/code     
            client_business_number: "123456RT001",  // 3 Business registration number

            client_company_name: "Sterling Group (Demo)",   // 4
            client_contact_name: "Rebecca Hughes",   // 5
            client_contact_title: "Manager",    // 6
            client_address: "101 Market Street, San Francisco, CA 94105",            // 7
            client_email: "rebecca.hughes@sterling.ai",  // 8
            client_mainphone: "555-123-4567",   // 9
            client_secondphone: "second phone", // 10
            client_fax: "fax",      // 11
            client_website: "https://SterlingAdv.ai",  // 12


            client_currency: "USD",   // 13
            client_tax_id: "123456RT001",   // 14 Tax identification number
            client_payment_term: 15,    // 15 Payment term in days
            client_payment_method: "Bank Transfer", // 16   Payment method

            client_template_id: "t1",   // 17
            client_terms_conditions: "Payment due in 7 days.",   // 18  
            client_note: "Preferred contact time: Morning",  // 19

            
            inv_number: "INV-1003",
            inv_title: "Invoice for Client 3",
            inv_date: new Date(),
            inv_due_date: new Date(),
            inv_payment_requirement: "Net 7 days",
            inv_payment_term: 7,
            inv_reference: "PO#-003",
            inv_currency: "GBP",

            inv_subtotal: 2.00,
            inv_discount: 0.0,
            inv_tax_label: "Tax",
            inv_tax_rate: 0.0,
            inv_tax_amount: 0.0,
            inv_shipping: 0.0,
            inv_handling: 0.0,
            inv_deposit: 0.0,
            inv_adjustment: 0.0,
            inv_other_charges_label: "Other Charges",
            inv_other_charges_amount: 0.0,
            inv_total: 2.00,

            inv_paid_total: 1.00,
            inv_balance_due: 1.00,
            inv_payment_status: "Partially Paid",

            inv_flag_word: "Partially Paid",
            inv_flag_emoji: "🟠",

            inv_pdf_template: "default",
            inv_notes: "Thank you for your business!",
            inv_terms_conditions: "Thank you for your business!",

            inv_items: [
                {
                    item_id: "ITEM",
                    item_number: "ITEM",
                    item_name: "🚧 Example Item (Tap to Edit)",
                    item_description: "This is a sample item to demonstrate how items work. You can edit or replace it.",
                    item_sku: "FBAPMK5M",
                    item_rate: 1.00,
                    item_unit: "unit",
                    item_note: "This item is for demo purposes only.",
                    item_quantity: 2,
                    item_amount: 2.00,
                },
            ],

            inv_payments: [
                {

                    pm_id: "pm_1002",
                    pm_name: "Bank Transfer",
                    pm_note: "Payment for invoice INV-1002",

                    pay_date: new Date(),
                    pay_amount: 1.00,
                    pay_reference: "TRX002",
                    pay_note: "First half",
                },
            ],
            ...baseFlags,
        },

    ],

};

export const seed_global = {
    plan25: [
        {
            plan_id: "plan25_1",
            plan_name: "Free",
            plan_price: "3 months free",
            plan_features: [
                "Up to 20 invoices per month",
                "Full library of professional templates",
                "AI-driven invoices, items & clients",
                "PDF export, email delivery, and sharing",
                "Branded invoices with your logo and style",
                "One-click invoice duplication",
                "Referral rewards — extend your free plan",
            ],
            ...baseFlags,
        },
        {
            plan_id: "plan25_2",
            plan_name: "Ad-Free",
            plan_price: "US$1.99 / month",
            plan_features: [
                "Ad-free",
                "No watermarks",
            ],
            ...baseFlags,
        },
    ],
};
