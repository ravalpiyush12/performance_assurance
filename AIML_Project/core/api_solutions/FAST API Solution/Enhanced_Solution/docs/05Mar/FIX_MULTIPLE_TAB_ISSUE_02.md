# 🔧 Fix: Multiple Tab Contents Showing on First Load

## 🎯 Problem
When page loads for the first time, it shows:
- ✅ Register Test tab content (correct)
- ❌ Oracle SQL tab content (should be hidden)

Both contents are visible at the same time!

---

## 🔍 Root Cause

The issue is that BOTH tabs have `class="tab-content active"` or there's no proper initialization.

---

## ✅ Solution: Ensure Only ONE Tab Content is Active

### Step 1: Check ALL Tab Contents

**File:** `index.html`

**Find ALL `<div id="..." class="tab-content">` sections:**

```html
<!-- Register Test Tab -->
<div id="registertest" class="tab-content active">  <!-- ✓ Should be active -->
    ...
</div>

<!-- Oracle SQL Tab -->
<div id="oracle" class="tab-content">  <!-- ✓ Should NOT be active -->
    ...
</div>

<!-- AppDynamics Tab -->
<div id="appdynamics" class="tab-content">  <!-- ✓ Should NOT be active -->
    ...
</div>

<!-- AWR Tab -->
<div id="awr" class="tab-content">  <!-- ✓ Should NOT be active -->
    ...
</div>

<!-- LoadRunner/PC Tab -->
<div id="loadrunner" class="tab-content">  <!-- ✓ Should NOT be active -->
    ...
</div>

<!-- MongoDB Tab -->
<div id="mongodb" class="tab-content">  <!-- ✓ Should NOT be active -->
    ...
</div>

<!-- Splunk Tab -->
<div id="splunk" class="tab-content">  <!-- ✓ Should NOT be active -->
    ...
</div>
```

---

## 🔧 Fix: Remove ALL "active" Classes Except Register Test

### CHANGE #1: Make ONLY Register Test Active

**FIND:**
```html
<div id="oracle" class="tab-content active">
```

**CHANGE TO:**
```html
<div id="oracle" class="tab-content">
```

**FIND:**
```html
<div id="registertest" class="tab-content">
```

**CHANGE TO:**
```html
<div id="registertest" class="tab-content active">
```

---

## 🔧 Alternative Fix: Add CSS to Ensure Only Active Tab Shows

If the issue persists, add this CSS to make absolutely sure only active tab shows:

**File:** `index.html`

**FIND the `<style>` section and ADD this CSS:**

```css
/* Ensure only active tab content shows */
.tab-content {
    display: none !important;
}

.tab-content.active {
    display: block !important;
}
```

---

## 🔧 Additional Fix: Initialize on Page Load

Add JavaScript to ensure only one tab is active on page load:

**File:** `index.html`

**FIND the `window.addEventListener('DOMContentLoaded'` section:**

```javascript
window.addEventListener('DOMContentLoaded', function() {
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
    loadLandingLOBs();
    loadCurrentTestRun();
    loadRecentRegistrations();
    loadRegistrationLOBs();
});
```

**ADD this NEW function BEFORE the DOMContentLoaded:**

```javascript
// Ensure only Register Test tab is active on load
function initializeTabs() {
    // Hide all tab contents first
    const allTabContents = document.querySelectorAll('.tab-content');
    allTabContents.forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    const allTabButtons = document.querySelectorAll('.tab');
    allTabButtons.forEach(button => {
        button.classList.remove('active');
    });
    
    // Show only Register Test tab
    const registerTab = document.getElementById('registertest');
    if (registerTab) {
        registerTab.classList.add('active');
    }
    
    // Make Register Test button active
    const registerButton = document.querySelector('[onclick*="registertest"]');
    if (registerButton) {
        registerButton.classList.add('active');
    }
    
    console.log('Tabs initialized - Register Test is active');
}

window.addEventListener('DOMContentLoaded', function() {
    // Initialize tabs FIRST
    initializeTabs();
    
    // Then load data
    loadEnvironmentInfo();
    loadDatabases();
    loadApiKeys();
    checkDatabaseStatus();
    loadLandingLOBs();
    loadCurrentTestRun();
    loadRecentRegistrations();
    loadRegistrationLOBs();
});
```

---

## 🧪 Testing Steps

### Step 1: Clear Browser Cache
```
Ctrl + Shift + Delete (Chrome/Edge)
Cmd + Shift + Delete (Mac)
```
Clear "Cached images and files"

### Step 2: Hard Reload
```
Ctrl + Shift + R (Windows)
Cmd + Shift + R (Mac)
```

### Step 3: Verify
1. Open the application
2. **Expected:** Only "Register Test" content is visible
3. **Expected:** Oracle SQL content is hidden
4. Click "Oracle SQL APIs" tab
5. **Expected:** Oracle content shows, Register Test hides

---

## 🔍 Debug: Check What's Wrong

If issue still persists, open browser console (F12) and run:

```javascript
// Check which tab contents have 'active' class
document.querySelectorAll('.tab-content.active').forEach(tab => {
    console.log('Active tab:', tab.id);
});

// Should output only: "Active tab: registertest"
```

If you see multiple tabs, then we need to find where the extra 'active' class is coming from.

---

## 📝 Quick Checklist

- [ ] Remove `active` class from `<div id="oracle" class="tab-content">`
- [ ] Ensure `active` class on `<div id="registertest" class="tab-content active">`
- [ ] Add CSS `.tab-content { display: none !important; }`
- [ ] Add `initializeTabs()` function in JavaScript
- [ ] Call `initializeTabs()` first in DOMContentLoaded
- [ ] Clear browser cache
- [ ] Hard reload page

---

## ✅ Expected Result

When you open the application:
```
✅ Register Test tab is selected (button is highlighted)
✅ Only Register Test content is visible
✅ Oracle SQL content is hidden
✅ All other tab contents are hidden

When you click Oracle SQL tab:
✅ Register Test content hides
✅ Oracle SQL content shows
```

---

## 🎯 Summary

The issue is that multiple `tab-content` divs have the `active` class on page load. The fix:

1. **Remove** `active` from all tabs except `registertest`
2. **Add CSS** to force display:none for inactive tabs
3. **Add JavaScript** to initialize tabs on page load

This ensures only ONE tab content is visible at a time! 🚀