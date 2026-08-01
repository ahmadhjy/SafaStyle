# Safa Style — Shop Manager Guide

A simple guide for managing the online shop. No tech experience needed.

---

## What is this?

This guide explains how to use the **admin panel** — the behind-the-scenes area where you add products, update prices, and check orders for **safastyle.com**.

Think of it like the back office of the website.

---

## How to log in

1. Open your web browser (Chrome, Safari, etc.)
2. Go to: **https://safastyle.com/admin/**
3. Enter your **username** and **password**
4. Click **Log in**

**Tip:** Use the **Storefront** link at the top to open the live website in a new tab — handy to check how something looks after you save it.

**Forgot your password?** Ask whoever set up your account (your developer or store owner). They can reset it for you.

---

## What you can do vs. what you cannot

Most shop managers can work with:

| You can manage | What it is |
|----------------|------------|
| **Products** | Add and edit items for sale |
| **Categories** | Groups like Sets, Dresses, Bags |
| **Colors & Sizes** | Options shoppers pick on product pages |
| **Orders** | Orders customers place online |

Some things only the **main admin** (owner/developer) can change:

- Store address, phone numbers, and email in the footer
- Privacy policy, terms, and exchange policy pages
- Creating new admin logins
- Homepage banner images

If you need any of those updated, ask the main admin.

---

## Your daily routine

### Morning check (5 minutes)

1. Log in to the admin
2. Open **Orders**
3. Look for new orders with status **Pending**
4. Update the status as you work on them (see [Handling orders](#handling-orders) below)

### When new stock arrives

1. Find the product in **Products**
2. Open it and go to the **Variations** section
3. Update **Stock** for each color/size
4. Click **Save**

---

## Adding a new product

### Before you start

Make sure the product’s **colors** and **sizes** already exist in the admin (under **Colors** and **Sizes**). If a color or size is missing, add it there first.

Also make sure the product is in the right **category** (e.g. Sets, Dresses).

---

### Step 1 — Create the product

1. Go to **Catalog** → **Products**
2. Click **Add product** (top right)
3. Fill in:

| Field | What to write |
|-------|----------------|
| **Name** | Product name as customers should see it (e.g. “Linen Two-Piece Set”) |
| **Short description** | One short line for product cards |
| **Description** | Full details — fabric, fit, styling notes |
| **Measurements** | Sizes in cm if helpful (e.g. “Top length: 75cm”) |
| **Categories** | Tick every category this product belongs in |

4. Scroll to **Pricing** and enter the **Base price** (normal selling price)
5. Under **Visibility**, tick **Is active** so customers can see it
6. Click **Save**

**Important:** Do not create a second product with the exact same name. If the item already exists, open it and edit it instead.

---

### Step 2 — Add photos

1. Stay on the product page (or open it again from the Products list)
2. Scroll to **Media**
3. Click **Add media**
4. Upload your photos (or pick from the library if they were uploaded before)
5. For each photo:
   - Click **Primary** on the best main photo
   - If the product comes in colors, assign each photo to the right **color**
6. Drag photos to reorder if needed
7. Click **Save**

**Photo tips:**

- Use clear, bright photos on a clean background
- Show the full outfit, not just a close-up
- For products with colors: assign photos to each color so the gallery changes when the customer picks a color
- Phone photos are fine — just make sure they are sharp and well lit

---

### Step 3 — Choose colors and sizes (if the product has options)

1. On the same product page, find **Colors & sizes**
2. Select all **colors** this product comes in
3. Select all **sizes** this product comes in
4. Click **Save**

If the product has only one version (no color or size choice), leave both empty.

---

### Step 4 — Build the variations (required!)

A **variation** is each combination you sell — for example “Black / M” or “Navy / L”.

1. After saving colors and sizes, scroll to **Variations**
2. Click **Generate variations**
3. The system creates one row per color + size combination
4. For each row, set:
   - **Price** — normal price (often same as base price)
   - **Sale price** — only if on sale; leave blank otherwise
   - **Stock** — how many you have in stock
5. Click **Save**

**Without this step, customers cannot add the product to their bag.**

**Faster way for many rows:** Use the boxes at the top of the Variations section to apply the same price, sale price, or stock to all rows at once, then click **Apply to all rows**.

---

### Simple product (one price, no color/size)

Example: one scarf, one price, one stock count.

1. Add the product and photos as above
2. Leave **Colors & sizes** empty
3. Save, then click **Generate variations** (creates one row)
4. Set **Stock** on that row
5. Save

---

## Putting a product on sale

1. Open the product
2. Go to **Variations**
3. Enter a **Sale price** lower than the normal **Price**
4. Save

The website will show the old price crossed out and a **Sale** badge.

**Optional:** Also tick **Is on sale** under Visibility — this helps the product appear in the shop’s “On sale” filter.

**Note:** Ticking “On sale” alone does **not** show a sale badge. You must set the **sale price**.

---

## Out of stock

1. Open the product
2. Go to **Variations**
3. Set **Stock** to **0** for the sold-out color/size
4. Save

Customers will see “Out of stock” and cannot order that option.

To bring it back, set stock to the real number again.

---

## Hiding a product (without deleting it)

1. Open the product
2. Uncheck **Is active** under Visibility
3. Save

The product disappears from the shop but stays in the admin so you can turn it back on later.

---

## Managing categories

Go to **Catalog** → **Categories**.

| Field | What it does |
|-------|----------------|
| **Name** | Category name (Sets, Bags, etc.) |
| **Image** | Optional photo for the homepage category section |
| **Is featured** | Highlights on the homepage |
| **Is active** | Must be on to show on the website |
| **Sort order** | Lower numbers appear first (e.g. 1, 2, 3) |

**Tip:** If you do not upload a category image, the site shows a simple icon instead.

---

## Handling orders

Go to **Orders**.

### What you see

Each order shows:

- Customer name and phone number
- Delivery address
- What they ordered (product, color, size, quantity)
- Total amount
- **Status** — where the order is in your process

### Order statuses — what to pick

| Status | When to use it |
|--------|----------------|
| **Pending** | Just received — not handled yet |
| **Confirmed** | You accepted the order |
| **Processing** | You are preparing the order |
| **Shipped** | Order has been sent out |
| **Delivered** | Customer received it |
| **Cancelled** | Order will not be fulfilled |

Change the status from the order list or inside the order. No need to change anything else — items and totals are filled in automatically.

### After a customer orders

- Stock goes down automatically when they place the order
- The store team gets an email notification
- If the customer entered an email, they get a confirmation too
- Payment is **cash on delivery** — no card payment on the website

**Your job:** Contact the customer if needed (phone is on the order), prepare the order, and update the status as you go.

---

## Colors and sizes

### Adding a new color

1. **Catalog** → **Colors** → **Add color**
2. Enter the **Name** (e.g. “Dusty Rose”)
3. Pick a **Hex code** (the color swatch shoppers see) — use the color picker
4. Save

### Adding a new size

1. **Catalog** → **Sizes** → **Add size**
2. Enter the **Name** (e.g. “M” or “38”)
3. Save

**Warning:** Do not delete a color or size that is already used on live products.

---

## Common problems and fixes

### “Customers can’t add this to their bag”

Usually one of these:

- **Stock is 0** → Set stock on the variation row
- **Variations were never created** → Save the product, then click **Generate variations**
- **Product is not active** → Tick **Is active**
- **That color/size row is inactive** → Check **Is active** on the variation row

### “I see two of the same product”

- Always **edit** the existing product instead of creating a new one
- If you accidentally created an empty duplicate, select it in the Products list, choose **Remove empty duplicates** from the Action menu, and click Go

### “Sale badge doesn’t show”

- Set **Sale price** on the variation (lower than **Price**)
- Save the product

### “Wrong photo shows for a color”

- Open the product → **Media**
- Make sure each photo is assigned to the correct **color**
- Save

### “Category doesn’t show in the top menu”

The top menu only shows categories that:

- Are **active**, and
- Have at least one **active product** in them

---

## What NOT to do

| Don’t | Why |
|-------|-----|
| Create two products with the same name | Causes confusion; the system may block it |
| Click **Generate variations & overwrite prices** unless you mean it | Resets all variation prices to the base price |
| Delete colors or sizes in use | Breaks existing products |
| Change **Slug** or **SKU** | These are automatic — leave them alone |
| Run commands on the server | Only for developers — can wipe products |
| Edit order line items or totals | System-generated — read only |

---

## Quick reference card

```
LOG IN:     safastyle.com/admin/
WEBSITE:    safastyle.com

NEW PRODUCT:
  Products → Add product → fill details → add photos
  → pick colors & sizes → Save → Generate variations → set stock → Save

ON SALE:    Set Sale price on variations (lower than Price)

OUT OF STOCK:  Stock = 0 on that variation

HIDE PRODUCT:  Uncheck "Is active"

ORDERS:     Orders → open order → change Status

NEED HELP WITH:
  - New login account
  - Footer address / phone / email
  - Homepage banners
  - Privacy policy / terms
  → Ask the main admin or developer
```

---

## Words you might see

| Word | Plain meaning |
|------|----------------|
| **Admin** | The management area behind the website |
| **Product** | An item you sell |
| **Variation** | One sellable version (e.g. Black in size M) |
| **Category** | A group in the shop (Sets, Dresses, etc.) |
| **Stock** | How many you have left |
| **Active** | Visible to customers |
| **Slug** | Web address piece — automatic, ignore it |
| **Media / Gallery** | Product photos |

---

*Safa Style — Shop Manager Guide. For technical or site-wide changes, contact your developer.*
