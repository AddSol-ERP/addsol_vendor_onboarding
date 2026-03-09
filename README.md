# Addsol Vendor Onboarding

A comprehensive ERPNext application for automated vendor onboarding with Cashfree API validation for Indian suppliers. This app streamlines the complete supplier registration process with automated credential validation, approval workflows, and integration with ERPNext's purchasing system.

## Overview

The **Addsol Vendor Onboarding App** (`addsol_vendor_onboarding`) is designed for businesses that require a robust, automated supplier onboarding process with Indian compliance validation. It provides end-to-end management of supplier registration, from initial invitation through automated GSTN, PAN, and bank account validation, to final approval and integration with the purchasing system.

![Addsol Vendor Onboarding](addsol_vendor_onboarding/documentation/images/addsol_vendor_onboarding.png)

### **Core Onboarding Features**

**Key capabilities include:**
- Complete supplier lifecycle management from invitation to approval
- Automated credential validation through Cashfree APIs
- Secure supplier portal for data submission
- Multi-stage approval workflow with role-based permissions
- Integration with ERPNext's Purchase Order system
- Comprehensive audit trail and validation logging
- Email notifications at every workflow stage
- Emergency override capabilities for critical situations

**Supported Validations:**
- GSTN (Goods and Services Tax Network) verification
- PAN (Permanent Account Number) validation
- Bank account and IFSC code verification
- Udyog Aadhaar certificate validation
- Document upload and verification

## Business Benefits

**For Procurement Teams:**
- Reduce manual supplier verification time by 90%
- Ensure compliance with Indian regulatory requirements
- Automated validation eliminates human error
- Complete audit trail for compliance and reporting
- Streamlined workflow reduces onboarding cycle time

**For Suppliers:**
- Self-service portal for convenient data submission
- Real-time validation feedback and status updates
- Secure credential management
- Clear communication throughout the process
- Mobile-friendly interface for accessibility

**For Management:**
- Enhanced visibility into supplier onboarding pipeline
- Risk mitigation through automated validations
- Emergency override capabilities for business continuity
- Comprehensive reporting and analytics
- Integration with existing ERPNext workflows

**Overall Benefits:**
- Unified platform for supplier management
- Reduced administrative overhead
- Improved data accuracy and consistency
- Enhanced security and compliance
- Scalable solution for growing supplier networks

## Features

### **Core Features**

**Supplier Management:**
- Automated supplier creation and invitation system
- Secure credential generation and delivery
- Supplier portal with role-based access
- Document management and attachment tracking
- Supplier status tracking and reporting

**Validation System:**
- Cashfree API integration for credential validation
- GSTN, PAN, and bank account verification
- Udyog Aadhaar certificate validation
- Real-time validation status updates
- Comprehensive validation logging
- Failed validation notification and retry mechanisms

**Workflow Automation:**
- Multi-stage approval workflow
- Email notifications at each workflow stage
- Role-based permission controls
- Emergency override for critical situations
- Re-verification process for updated information
- Purchase Order integration and restrictions

**Integration Features:**
- Seamless ERPNext Supplier integration
- Purchase Order control and restrictions
- Email system integration for notifications
- Role-based access control
- Audit trail and compliance logging
- Document management integration

### **Validation Capabilities**

**GSTN Validation:**
- Real-time GSTN verification through Cashfree APIs
- Automatic GST certificate validation
- GST status and registration date verification
- Business name and address matching

**PAN Validation:**
- PAN card number format validation
- Name matching with PAN records
- PAN status verification
- Tax payer category verification

**Bank Account Validation:**
- Bank account number verification
- IFSC code validation
- Bank name and branch verification
- Account holder name matching

**Document Validation:**
- GST certificate upload and verification
- PAN card attachment and validation
- Bank statement verification
- Udyog Aadhaar certificate validation

## 🔧 Requirements

- **ERPNext**: Version 15.x
- **Frappe Framework**: Compatible with ERPNext 15
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **Cashfree Account**: With API access for verification services

## Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch version-15
bench install-app addsol_vendor_onboarding
```

### Prerequisites

- ERPNext Version 15
- Python 3.10 or higher
- Node.js 18.x or higher
- Cashfree Account with API access for verification services
- Basic understanding of ERPNext supplier management
- System Manager permissions for configuration

### Quick Start

1. Install the app using the commands above
2. Configure Cashfree API credentials in Cashfree Settings
3. Create and assign required roles (Purchase Manager, Vendor Management)
4. Configure email account for notifications
5. Create your first supplier and initiate onboarding
6. Test the complete workflow with sample data

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
3. Role Name: `Vendor Management`
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
- Role: `Vendor Management`
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

### Vendor Management Role
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

## Integration

### **ERPNext Integration**
- **Supplier Module**: Direct integration with ERPNext's Supplier doctype
- **Purchase Orders**: Automatic restriction enforcement for unapproved suppliers
- **Email System**: Seamless integration with ERPNext's email infrastructure
- **Role System**: Utilizes ERPNext's role-based access control
- **Document Management**: Integration with ERPNext's file management system
- **Audit Trail**: Complete logging within ERPNext's audit framework

### **External Integration**
- **Cashfree APIs**: Real-time validation through Cashfree's verification services
- **SMTP Servers**: Support for external email service providers
- **Bank Systems**: Ready for integration with banking verification APIs
- **GST Portal**: Prepared for GST portal integration

### **Technical Integration**
- **Background Jobs**: Utilizes RQ for asynchronous validation processing
- **Webhooks**: Support for real-time status updates
- **API Endpoints**: RESTful APIs for external system integration
- **Database**: Optimized database queries for performance
- **Caching**: Intelligent caching for improved response times

## Security

### **Data Protection**
- **API Credentials**: Stored securely using Frappe's Password field with encryption
- **Role-Based Access**: Strict permission controls for different user roles
- **Data Validation**: Format validation before API calls to prevent injection
- **Audit Trail**: Complete logging of all validations and system actions
- **Email Security**: Credentials sent via secure email channels

### **Compliance & Privacy**
- **GDPR Compliance**: Data handling practices compliant with privacy regulations
- **Data Minimization**: Only collect necessary supplier information
- **Secure Storage**: All sensitive data encrypted at rest
- **Access Logs**: Complete audit trail of all data access
- **Retention Policies**: Configurable data retention and cleanup

### **API Security**
- **Rate Limiting**: Protection against API abuse and excessive calls
- **Input Validation**: Comprehensive validation of all user inputs
- **Error Handling**: Secure error messages that don't expose sensitive information
- **HTTPS Only**: All external API calls use secure HTTPS connections
- **Token Management**: Secure API token handling and refresh mechanisms

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

## Support and Contributing

### **Contributing**

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/addsol_vendor_onboarding
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### **Support**

For support and queries:
- **Documentation**: Refer to the comprehensive user guides and API documentation
- **Issues**: Report bugs and feature requests on the repository
- **Community**: Join our community for discussions and best practices
- **Email**: erpnext@aitspl.com for direct support

## 🤝 Support

For issues, questions, or contributions:

- **Email**: erpnext@aitspl.com
- **Company**: Addition Solutions
- **Website**: www.aitspl.com

## 📄 License

MIT License

Copyright (c) 2026 Addition Solutions

## 🙏 Credits

**Developed by Addition Solutions**
*Innovative solutions for modern business challenges*

Visit us at: [https://aitspl.com](https://aitspl.com)

Commercial ERPNext customization and implementation services available.
Contact: erpnext@aitspl.com
---

**Version**: 1.2.1  
**Last Updated**: February 2026  
**ERPNext Version**: 15.x  
**Status**: Production Ready

