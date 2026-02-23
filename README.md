# DeVoltrans Vendor Onboarding for ERPNext 15

Custom ERPNext app for automated vendor onboarding with Cashfree API validation for Indian suppliers.

## 📋 Overview

This custom app implements a complete vendor onboarding workflow for DeVoltrans Pvt. Ltd. with automated validation of supplier credentials through Cashfree APIs.

## ✨ Features

- ✅ **Automated Supplier Creation**: Purchase Manager initiates onboarding
- ✅ **Credential Management**: Automatic email with login credentials
- ✅ **Supplier Portal**: Suppliers can submit their data online
- ✅ **Cashfree API Integration**: Validates GSTN, PAN, and Bank Account
- ✅ **Approval Workflow**: Purchase Manager review and approval
- ✅ **Email Notifications**: Status updates at each stage
- ✅ **Purchase Order Control**: Only approved suppliers can receive POs
- ✅ **Emergency Override**: Management role can bypass restrictions
- ✅ **Re-verification**: Update locked supplier details
- ✅ **Audit Trail**: Complete validation logging

## 🔧 Requirements

- **ERPNext**: Version 15.x
- **Frappe Framework**: Compatible with ERPNext 15
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **Cashfree Account**: With API access for verification services

## 📦 Installation

### Step 1: Get the App

```bash
cd ~/frappe-bench
bench new-app addsol_vendor_onboarding
```

When prompted, provide:
- **App Title**: Vendor Onboarding
- **App Description**: Vendor on boarding process for new supplier in India
- **App Publisher**: Addition Solutions
- **App Email**: contact@aitspl.com
- **App License**: MIT

### Step 2: Copy Files

Copy all the files from the artifacts to your app directory following the structure provided.

### Step 3: Install the App

```bash
bench --site your-site-name install-app addsol_vendor_onboarding
```

### Step 4: Run Migrations

```bash
bench --site your-site-name migrate
```

### Step 5: Build Assets

```bash
bench build --app addsol_vendor_onboarding
```

### Step 6: Restart Services

```bash
bench restart
```

## ⚙️ Configuration

### 1. Enable Developer Mode (Optional)

For development, edit `sites/your-site-name/site_config.json`:

```json
{
  "developer_mode": 1
}
```

### 2. Configure Cashfree Settings

1. Login to ERPNext
2. Navigate to: **Vendor Onboarding > Cashfree Settings**
3. Enter your credentials:
   - **API URL**: `https://api.cashfree.com` (production) or `https://sandbox.cashfree.com` (testing)
   - **Client ID**: Your Cashfree Client ID
   - **Client Secret**: Your Cashfree Client Secret
   - **Is Sandbox**: Check if using test environment
4. Enable required validations:
   - ☑️ Enable GSTN Validation
   - ☑️ Enable PAN Validation
   - ☑️ Enable Bank Validation
5. Save the settings

### 3. Create Custom Role

1. Go to: **Setup > Role**
2. Click **New**
3. Role Name: `DeVoltrans Management`
4. Save

### 4. Configure Email Account

1. Go to: **Setup > Email Account**
2. Configure your SMTP settings
3. Test email sending

### 5. Assign Roles to Users

**Purchase Managers:**
- Role: `Purchase Manager`
- Permissions: Create, approve, reject onboarding

**Suppliers:**
- Role: `Supplier`
- Permissions: View and update own onboarding record

**Management:**
- Role: `DeVoltrans Management`
- Permissions: All + Emergency PO creation

## 📖 Usage Guide

### For Purchase Managers

#### Starting Onboarding Process

1. Create a new **Supplier** or open existing one
2. Click **Actions > Start Onboarding**
3. Fill in the initial details:
   - Supplier Name
   - Email
   - Phone Number
4. Save - System sends credentials automatically

#### Reviewing Submissions

1. Wait for email notification: "Supplier Ready for Review"
2. Open the **Supplier Onboarding** document
3. Review:
   - ✓ Validation status (GSTN, PAN, Bank)
   - 📄 Attached documents
   - 📝 Supplier details
4. Click **Approve** or **Reject**

#### Re-verification Process

1. Open approved **Supplier Onboarding**
2. Click **Re-initiate Verification**
3. Provide reason for re-verification
4. Supplier will be notified to update information

### For Suppliers

#### Initial Submission

1. Receive email with login credentials
2. Click login URL in email
3. Login to ERPNext portal
4. Fill mandatory fields:
   - GSTN (15 characters)
   - PAN (10 characters)
   - Bank Account Number
   - Bank IFSC Code (11 characters)
   - Udyog Aadhaar
   - Phone Number
5. Attach required documents:
   - GSTN Certificate
   - PAN Card
   - Bank Statement
   - Udyog Aadhaar Certificate
6. Save - Validation starts automatically

#### After Validation

- ✅ **Success**: Wait for Purchase Manager approval
- ❌ **Failed**: Update information and resubmit

#### Re-verification

1. Receive email notification
2. Login and update required information
3. Save to trigger re-validation

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                     VENDOR ONBOARDING WORKFLOW                   │
└─────────────────────────────────────────────────────────────────┘

1. Purchase Manager Creates Supplier
   ↓
2. System Sends Credentials → Email to Supplier
   ↓
3. Supplier Logs In & Submits Data
   ↓
4. Automatic Cashfree API Validation
   ├─ GSTN Verification
   ├─ PAN Verification
   └─ Bank Account Verification
   ↓
5. Validation Result
   ├─ SUCCESS → Notify Purchase Manager
   │             ↓
   │          Purchase Manager Reviews
   │             ├─ APPROVE → Supplier Activated
   │             └─ REJECT → Process Ends
   │
   └─ FAILED → Notify Supplier & Purchase Manager
                ↓
             Supplier Updates & Resubmits
                ↓
             (Go to step 4)
```

## 🚫 Purchase Order Restrictions

### Standard Users
- ❌ Cannot create PO for unapproved suppliers
- ✅ Can only create PO for approved suppliers

### DeVoltrans Management Role
- ✅ Can create emergency POs
- ⚠️ Warning displayed for unapproved suppliers

## 📊 Validation Logs

All API validations are logged in **Supplier Validation Log**:

- 🕒 Timestamp
- 📋 Validation Type (GSTN/PAN/Bank)
- ✅/❌ Status
- 📄 Request & Response Data
- ⚠️ Error Messages (if failed)

## 🔍 Troubleshooting

### Issue: Validation Not Triggering

**Solution:**
```bash
# Check background workers
bench doctor

# Check queue
bench --site your-site-name console
>>> frappe.get_all('RQ Job', limit=10)

# Restart workers
bench restart
```

### Issue: Emails Not Sending

**Solution:**
1. Verify Email Account configuration
2. Test SMTP connection
3. Check Error Logs: **Setup > Error Log**
4. Verify email queue: **Email Queue** doctype

### Issue: API Validation Failing

**Solution:**
1. Check Cashfree Settings
2. Verify API credentials
3. Check network connectivity
4. Review Supplier Validation Logs
5. Check API rate limits

### Issue: Permission Errors

**Solution:**
1. Verify role assignments
2. Check DocType permissions
3. Clear cache:
   ```bash
   bench --site your-site-name clear-cache
   ```

### Issue: Fields Not Showing

**Solution:**
```bash
# Rebuild and migrate
bench --site your-site-name migrate
bench build --app addsol_vendor_onboarding
bench restart

# Hard refresh browser (Ctrl + Shift + R)
```

## 🗂️ File Structure

```
addsol_vendor_onboarding/
├── addsol_vendor_onboarding/
│   ├── __init__.py
│   ├── hooks.py
│   ├── modules.txt
│   ├── patches.txt
│   ├── config/
│   │   ├── __init__.py
│   │   ├── desktop.py
│   │   └── docs.py
│   ├── vendor_onboarding/
│   │   ├── __init__.py
│   │   └── doctype/
│   │       ├── __init__.py
│   │       ├── supplier_onboarding/
│   │       │   ├── __init__.py
│   │       │   ├── supplier_onboarding.py
│   │       │   ├── supplier_onboarding.js
│   │       │   ├── supplier_onboarding.json
│   │       │   └── supplier_onboarding_list.js
│   │       ├── supplier_validation_log/
│   │       │   ├── __init__.py
│   │       │   ├── supplier_validation_log.py
│   │       │   ├── supplier_validation_log.js
│   │       │   └── supplier_validation_log.json
│   │       └── cashfree_settings/
│   │           ├── __init__.py
│   │           ├── cashfree_settings.py
│   │           ├── cashfree_settings.js
│   │           └── cashfree_settings.json
│   ├── api/
│   │   ├── __init__.py
│   │   ├── cashfree_api.py
│   │   └── supplier_portal.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── email_utils.py
│   │   └── validation_utils.py
│   └── public/
│       ├── js/
│       │   ├── supplier.js
│       │   └── purchase_order.js
│       └── css/
│           └── vendor_onboarding.css
├── requirements.txt
├── pyproject.toml
├── setup.py
├── license.txt
└── README.md
```

## 🔐 Security Considerations

1. **API Credentials**: Stored securely using Frappe's Password field
2. **Role-Based Access**: Strict permission controls
3. **Data Validation**: Format validation before API calls
4. **Audit Trail**: Complete logging of all validations
5. **Email Security**: Credentials sent via secure email

## 🧪 Testing

### Manual Testing Checklist

- [ ] Create supplier and initiate onboarding
- [ ] Verify email credentials sent
- [ ] Login as supplier and submit data
- [ ] Check validation process completes
- [ ] Test approval workflow
- [ ] Test rejection workflow
- [ ] Verify PO restrictions work
- [ ] Test emergency PO creation
- [ ] Test re-verification process
- [ ] Verify all email notifications

### Test Cashfree Connection

1. Go to **Cashfree Settings**
2. Click **Test Connection** button
3. Verify success message

## 📈 Future Enhancements

- [ ] Bulk supplier onboarding
- [ ] Supplier performance scoring
- [ ] Document expiry tracking
- [ ] Multi-level approval workflow
- [ ] Integration with GST portal
- [ ] Supplier self-service portal
- [ ] Mobile app support
- [ ] Advanced analytics dashboard

## 🤝 Support

For issues, questions, or contributions:

- **Email**: contact@aitspl.com
- **Company**: Addition Solutions
- **Website**: www.aitspl.com

## 📄 License

MIT License

Copyright (c) 2025 Addition Solutions

## 🙏 Credits

Developed by **Addition Solutions** for **DeVoltrans Pvt. Ltd.**

---

**Version**: 0.0.1  
**Last Updated**: January 2025  
**ERPNext Version**: 15.x  
**Status**: Production Ready