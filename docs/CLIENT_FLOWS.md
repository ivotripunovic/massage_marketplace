# Massage Marketplace - Client User Flows

## Overview

This document describes the user flows for clients (public users) browsing the massage marketplace. Unlike providers who require authentication, clients can browse and view provider profiles without creating an account.

---

## 1. Browse Provider Directory

**Overview**: Public marketplace where anyone can discover massage therapy providers.

**Path**: `/` or `/providers/`

**Prerequisites**: None (no authentication required)

**Steps**:
1. User visits homepage or providers directory
2. System displays grid of active, verified providers
3. Each provider card shows:
   - Profile photo (or default avatar)
   - Provider name
   - Average rating with star indicator
   - Number of reviews
   - Number of services offered
   - "View Profile" button
4. Providers are displayed 20 per page
5. Pagination controls allow browsing multiple pages
6. All providers shown have `subscription_status='active'` and `is_email_verified=True`

**What's Displayed**:
- **Provider Cards** (grid layout, responsive):
  - Photo: Profile image or placeholder avatar
  - Name: First/last name or email username fallback
  - Rating: Average star rating (e.g., "★ 4.5 (12 reviews)")
  - Services: Count of active services
  - Button: "View Profile" links to detail page

**Technical Details**:
- No login required - completely public
- Query optimized with `select_related('user')` and `prefetch_related('services', 'reviews')`
- Pagination: 20 providers per page
- Only active and verified providers shown
- Ordered by created date (newest first)

**Related Views**:
- `ProviderDirectoryView` (`clients/views.py`)

**Database Queries**:
- Filters: `subscription_status='active'` AND `is_email_verified=True`
- Optimized with select/prefetch related
- ~3-4 queries per page load

---

## 2. View Provider Profile

**Overview**: Detailed public profile showing provider's services, certifications, and reviews.

**Path**: `/providers/<email>/`

**Prerequisites**: None (no authentication required)

**Steps**:
1. User clicks "View Profile" from directory or navigates to provider URL
2. System loads provider detail page
3. Page displays:
   - **Provider Header**: Photo, name, rating, contact info
   - **About Section**: Bio and professional information
   - **Services Section**: All active services with pricing
   - **Certifications Section**: Images of professional certifications
   - **Reviews Section**: All reviews with ratings and comments
4. User can contact provider via email button
5. Breadcrumb navigation allows returning to directory

**What's Displayed**:

### Provider Header
- Large profile photo or avatar
- Full name (or email fallback)
- Average rating with stars
- Total review count
- Email address
- Phone number (if provided)
- "Contact Provider" button (mailto link)

### About Section
- Bio text (if provided)
- Professional background and specialties

### Services Section
- Grid of service cards showing:
  - Service type (e.g., "Swedish Massage")
  - Duration (e.g., "60 minutes")
  - Price (e.g., "$75.00")
  - Description (if provided)
- Only active services are shown
- Ordered by service type

### Certifications Section
- Grid of certification images
- Certification name under each image
- Professional credentials and licenses
- Visual proof of qualifications

### Reviews Section
- List of all reviews (newest first)
- Each review shows:
  - Star rating (1-5 stars, visual)
  - Review date
  - Client name (if provided)
  - Review comment
- Empty state if no reviews yet

**Navigation**:
- Breadcrumb: Home > Providers > [Provider Name]
- Back to providers directory
- Contact provider via email

**Technical Details**:
- Returns 404 if provider is inactive or unverified
- Query optimized with `select_related('user')` and `prefetch_related('services', 'certifications', 'reviews')`
- All related data loaded in single query set
- Mobile responsive layout

**Related Views**:
- `ProviderDetailView` (`clients/views.py`)

**Database Queries**:
- Filters: `subscription_status='active'` AND `is_email_verified=True`
- Prefetch: services, certifications, reviews
- ~4-5 queries per page load

---

## 3. Contact Provider

**Overview**: Direct communication with massage therapist via email.

**Path**: Triggered from provider detail page

**Prerequisites**: None (no authentication required)

**Steps**:
1. User views provider profile
2. User clicks "Contact Provider" button
3. System opens user's default email client with mailto link
4. Email is pre-addressed to provider's email
5. User composes and sends email directly
6. Provider receives email in their inbox

**Technical Details**:
- Uses `mailto:` link - no server-side processing
- No tracking or logging of communication
- Direct email communication
- No in-app messaging system (future enhancement)

**Example mailto link**:
```html
<a href="mailto:provider@example.com">Contact Provider</a>
```

---

## 4. View Ratings and Reviews

**Overview**: Read reviews from other clients about provider's services.

**Path**: Part of provider detail page (`/providers/<email>/`)

**Prerequisites**: None (no authentication required)

**Steps**:
1. User scrolls to Reviews section on provider profile
2. System displays all reviews for this provider
3. Each review shows:
   - Star rating (visual stars)
   - Date posted
   - Client name (optional)
   - Review comment
4. Reviews are ordered newest first
5. Empty state shown if no reviews exist

**Review Display Format**:
```
★★★★★   November 15, 2025
Jane Smith
"Excellent service! Very professional and knowledgeable.
The Swedish massage was exactly what I needed after a long week."
```

**Technical Details**:
- Reviews displayed on provider detail page
- No pagination (all reviews shown)
- Star rating: 1-5 filled stars, remainder empty
- Anonymous reviews allowed (client_name optional)
- No authentication required to view

---

## Common User Journeys

### Journey 1: First-Time Visitor Looking for Massage Therapist

1. User searches Google for "massage therapist near me"
2. Finds massage marketplace website
3. Lands on homepage (`/`)
4. Browses provider cards
5. Notices highly-rated provider
6. Clicks "View Profile"
7. Reviews services and certifications
8. Reads client reviews
9. Clicks "Contact Provider"
10. Sends inquiry via email

**Time to contact**: ~2-3 minutes

### Journey 2: Comparing Multiple Providers

1. User visits homepage
2. Opens 3-4 provider profiles in new tabs
3. Compares:
   - Ratings and review counts
   - Service offerings and prices
   - Certifications and credentials
   - Client testimonials
4. Selects preferred provider
5. Contacts via email

**Time to compare**: ~5-10 minutes

### Journey 3: Returning Visitor

1. User bookmarks or remembers provider's direct URL
2. Visits `/providers/<email>/` directly
3. Checks if new reviews posted
4. Books appointment via email/phone

**Time to book**: ~1 minute

---

## Navigation Structure

```
Home (/)
├── Provider Directory (/providers/)
│   └── Provider Detail (/providers/<email>/)
│       ├── About
│       ├── Services
│       ├── Certifications
│       └── Reviews
```

**Breadcrumb Example**:
```
Home > Providers > John Doe
```

---

## Responsive Design

### Desktop (≥1024px)
- Provider cards: 4 columns
- Full-width layout
- Side-by-side sections
- Large images

### Tablet (768px - 1023px)
- Provider cards: 2 columns
- Stacked sections
- Medium images

### Mobile (<768px)
- Provider cards: 1 column
- Fully stacked layout
- Optimized images
- Touch-friendly buttons
- Simplified navigation

---

## Accessibility Features

- Semantic HTML (nav, main, section)
- Alt text on all images
- Keyboard navigation
- Screen reader friendly
- High contrast colors
- Touch targets ≥44x44px

---

## Performance Optimizations

### Provider Directory
- Pagination (20 per page)
- Image lazy loading (future)
- Query optimization (select_related, prefetch_related)
- Database indexes on subscription_status

### Provider Detail
- Single query for all data
- Prefetch related services, certifications, reviews
- Cached rating calculations (future)
- Optimized image sizes

---

## Error Handling

### Provider Not Found (404)
**Triggers**:
- Invalid email in URL
- Provider doesn't exist
- Provider is inactive (`subscription_status != 'active'`)
- Provider email not verified (`is_email_verified = False`)

**Display**:
- Standard 404 page
- "Provider not found" message
- Link back to directory

### No Providers Available
**Triggers**:
- No active providers in database
- All providers inactive or unverified

**Display**:
- Empty state with icon
- "No Providers Available" message
- "Check back soon" text

### No Reviews Yet
**Triggers**:
- Provider has zero reviews

**Display**:
- Empty state message
- "No reviews yet. Be the first to review!"

---

## Future Enhancements

### Week 6+ Features (Coming Soon)
1. **Search & Filtering**:
   - Filter by service type
   - Filter by location (country, city)
   - Filter by price range
   - Multi-filter combinations

2. **Review Submission** (Week 7):
   - Allow clients to leave reviews
   - Star rating + comment
   - Client name optional
   - One review per client per provider

3. **Booking System** (Future):
   - In-app scheduling
   - Calendar integration
   - Availability display
   - Booking confirmations

4. **Favorites/Bookmarks** (Future):
   - Save favorite providers
   - Comparison tool
   - Email notifications

---

## Testing the Client Flows

### Manual Testing

#### Test 1: Browse Providers
```bash
1. Visit http://localhost:8000/
2. Verify provider cards display
3. Check pagination works (if 20+ providers)
4. Verify only active providers shown
5. Click "View Profile" button
```

#### Test 2: View Provider Detail
```bash
1. From directory, click any provider
2. Verify all sections display:
   - Photo, name, rating
   - Bio
   - Services with pricing
   - Certifications
   - Reviews
3. Verify breadcrumb works
4. Click "Contact Provider"
5. Verify mailto opens email client
```

#### Test 3: Mobile Responsiveness
```bash
1. Resize browser to mobile size (375px)
2. Verify:
   - Cards stack vertically
   - Images resize properly
   - Buttons are touch-friendly
   - No horizontal scroll
   - Navigation works
```

### Automated Testing

Run client tests:
```bash
cd /home/ivo/projects/directory_listing
./test.sh clients
```

**Coverage**: 19 tests covering:
- Provider directory view
- Provider detail view
- Filtering (active/verified only)
- Pagination
- No authentication required
- Model helper methods

---

## Database Schema (Client-Relevant)

### Provider (publicly visible fields)
- `user.email` - Contact email
- `user.first_name`, `user.last_name` - Name display
- `photo` - Profile image
- `bio` - About text
- `phone` - Contact phone
- `subscription_status` - Active/inactive (filter)
- `created_at` - Join date

### Service (publicly visible)
- `service_type` - Type of massage
- `description` - Service details
- `price` - Cost in USD
- `duration_minutes` - Session length
- `is_active` - Display filter

### Certification (publicly visible)
- `name` - Certification title
- `image` - Certificate image
- `uploaded_at` - Date added

### Review (publicly visible)
- `rating` - 1-5 stars
- `comment` - Review text
- `client_name` - Reviewer name (optional)
- `created_at` - Review date

---

## Security & Privacy

### What Clients CAN See
- Active, verified providers only
- Public profile information
- Services, certifications, reviews
- Contact information (email, phone)

### What Clients CANNOT See
- Inactive providers
- Unverified providers
- Provider dashboard/settings
- Subscription status details
- Payment information
- Other providers' private data

### Data Protection
- No personal client data collected for browsing
- Email communication happens outside system
- No tracking or analytics (currently)
- GDPR compliant (public data only)

---

## Support & Troubleshooting

### "Provider not found" Error
**Solution**: Provider may be inactive or unverified. Only active providers with verified emails are shown.

### "No providers available"
**Solution**: No active providers in system. Check back later or contact support.

### Can't see some providers
**Solution**: Only providers with active subscriptions and verified emails are visible.

### Contact button doesn't work
**Solution**: Ensure default email client is configured, or manually copy email address.

---

## Conclusion

The client user flow provides a simple, intuitive way for potential clients to:
1. **Discover** massage therapists through the public directory
2. **Evaluate** providers based on ratings, services, and certifications
3. **Contact** providers directly via email

No authentication is required, making it accessible to all users. The interface is mobile-responsive, accessible, and optimized for performance.
