# Massage Service Marketplace - Product Requirements Document

**Document Version:** 1.0  
**Last Updated:** January 2026  
**Status:** MVP Definition

---

## 1. Overview

**Product Name:** Massage Service Marketplace (TBD - final branding)

**Vision:** A simple, crypto-friendly marketplace connecting massage service providers with clients, enabling providers to monetize their services through a transparent subscription model while offering clients access to verified professionals.

**Target Launch:** 3 months from initiation

**Approach:** Minimum Viable Product (MVP) with essential features only. Server-side rendered HTML with minimal JavaScript to ensure fast time-to-market and broad compatibility.

---

## 2. Business Model

### Revenue Model
- **Pricing:** Monthly subscription fee charged to service providers
- **Subscription Cost:** $29-49/month (to be finalized based on market research)
- **Target Market:** Independent massage therapists, freelancers, and small clinics in high-demand regions

### Payment Processing

#### Provider Payments (Subscription)
- **Cryptocurrency Support:**
  - Bitcoin (BTC)
  - Ethereum (ETH)
  - USDC (Stablecoin)
  - Payment processor: TBD (options: BTCPay Server, Coinbase Commerce, or similar)
  
- **Bank Transfers:**
  - Manual verification process by admin team
  - Provider submits bank details in secure form
  - Admin reviews and confirms receipt monthly
  - Supports all major bank transfers (domestic and international, region-dependent)

#### Client Pricing
- **Completely Free:** No charges to browse, search, view profiles, or book services
- Future monetization: Service fee percentage (out of scope for MVP)

### Financial Operations (MVP)
- No automatic payment failures/retries in MVP (manual admin handling)
- Subscription renewal: Monthly, manually tracked in admin dashboard
- Payment verification workflow for bank transfers
- Dispute resolution: Manual admin review

---

## 3. Core User Stories

### Provider Stories
1. **As a provider**, I want to create an account with my basic information (name, email, phone) so I can access the marketplace.
2. **As a provider**, I want to upload my profile details (bio, photo, certifications) to build credibility with potential clients.
3. **As a provider**, I want to create and manage service listings with details (type, price, duration) so clients can understand my offerings.
4. **As a provider**, I want to set my subscription payment method (crypto or bank transfer) and manage my subscription status (active/inactive).
5. **As a provider**, I want to view my active subscription status and upcoming renewal dates.
6. **As a provider**, I want to deactivate my account when I'm not accepting new clients.

### Client Stories
1. **As a client**, I want to browse available providers without creating an account to see what services are available.
2. **As a client**, I want to search and filter providers by service type, location (country/city), and price range.
3. **As a client**, I want to view a provider's full profile including bio, certifications, photo, and reviews before booking.
4. **As a client**, I want to leave a rating and review after receiving a service from a provider.
5. **As a client**, I want to contact a provider via email or phone to book and discuss service details.

### Admin Stories
1. **As an admin**, I want to view all registered providers and their subscription status.
2. **As an admin**, I want to process and verify bank transfer payments from providers.
3. **As an admin**, I want to deactivate non-compliant provider accounts.
4. **As an admin**, I want to view basic platform metrics (active providers, listings, reviews).
5. **As an admin**, I want to monitor and resolve disputes or issues reported by clients or providers.

---

## 4. Minimum Features

### 4.1 Provider Portal

#### Account Management
- [ ] Sign up / Login (email-based authentication)
- [ ] Email verification flow
- [ ] Profile completion: Name, Phone Number, Bio, Profile Photo
- [ ] Certification upload (images/documents)
- [ ] Account deactivation/reactivation

#### Service Management
- [ ] Create service listing: Service Type, Description, Price, Duration (30min/60min/90min)
- [ ] Edit existing service listings
- [ ] Toggle service availability (active/inactive)
- [ ] View all own listings

#### Subscription & Payment
- [ ] Crypto wallet integration (display wallet address for BTC, ETH, USDC)
- [ ] Bank transfer payment method setup (bank account details form)
- [ ] View subscription status: Active/Inactive/Expired
- [ ] View subscription renewal date
- [ ] Subscription tier options (basic MVP: single tier)
- [ ] Payment history/receipt downloads (basic)

#### Dashboard
- [ ] Simple dashboard showing:
  - Current subscription status
  - Number of active listings
  - Average rating
  - Recent reviews

### 4.2 Client App (Public Marketplace)

#### Browsing & Discovery
- [ ] Public provider directory (no login required to browse)
- [ ] Provider cards with: Photo, Name, Average Rating, Service Types

#### Search & Filter
- [ ] Search by provider name
- [ ] Filter by Service Type (dropdown: Swedish, Deep Tissue, Thai, Reflexology, etc.)
- [ ] Filter by Location: Country selector, then City selector
- [ ] Filter by Price Range (slider or preset ranges)
- [ ] Combined filtering (service + location + price)

#### Provider Profile View
- [ ] Provider name, photo, bio
- [ ] Certifications displayed
- [ ] Full list of services: Type, Price, Duration
- [ ] Average rating and review count
- [ ] Contact information: Phone Number, Email
- [ ] Full reviews list with ratings and client comments
- [ ] "Contact Provider" button with pre-filled subject

#### Reviews & Ratings
- [ ] Simple 5-star rating system
- [ ] Text review field (250 char limit for MVP)
- [ ] Reviewer name (optional) and date
- [ ] Review submission form after service completion
- [ ] Email verification for reviewers (optional link to prevent spam)

#### Technical UX
- [ ] Fully responsive design (mobile-first)
- [ ] Zero JavaScript (server-side rendered HTML forms)
- [ ] Fast page load times
- [ ] Basic accessibility compliance (WCAG 2.1 AA)

### 4.3 Admin Dashboard (Internal Only)

#### Provider Management
- [ ] List all providers with status (active/inactive/suspended)
- [ ] Provider subscription status and payment method
- [ ] Ability to suspend/unsuspend provider
- [ ] View provider details and listings
- [ ] Search/filter providers by name, status, payment method

#### Payment Management
- [ ] Bank transfer verification workflow
  - [ ] List pending bank transfers
  - [ ] Approve/reject with comments
  - [ ] Confirmation email to provider
- [ ] Crypto payment tracking (manual monitoring)
- [ ] Subscription renewal status
- [ ] Payment history export (CSV)

#### Content Moderation
- [ ] Flag/review suspicious profiles
- [ ] Review reported content or disputes
- [ ] Ability to remove listings or reviews
- [ ] Basic audit log of admin actions

#### Analytics (Basic)
- [ ] Active provider count
- [ ] Total listings
- [ ] Average provider rating
- [ ] Monthly revenue (subscription count × price)
- [ ] Payment method breakdown (crypto vs bank)
- [ ] Geographic distribution of providers
- [ ] Review metrics (avg rating, total reviews)

---

## 5. Technical Architecture

### 5.1 Tech Stack (MVP)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Frontend** | HTML5 + CSS3 (Tailwind) | Server-side rendered, minimal JS, fast deployment |
| **Backend** | Python (Django/FastAPI) or Node.js (Express) | Rapid development, good ecosystem |
| **Database** | PostgreSQL | Relational data, ACID compliance, free |
| **Storage** | S3 or self-hosted object storage | Profile photos, certifications |
| **Crypto Integration** | BTCPay Server or Coinbase Commerce | Self-hosted or managed payment processor |
| **Hosting** | AWS/DigitalOcean/Heroku | Simple, scalable, cost-effective |
| **Email** | SendGrid or similar | Transactional emails |
| **CDN** | CloudFlare | Global distribution, DDoS protection |

### 5.2 Core Modules

```
marketplace/
├── auth/                    # User authentication & sessions
├── providers/               # Provider profiles & listings
├── clients/                 # Client browsing & reviews
├── payments/                # Subscription & payment processing
├── admin/                   # Admin dashboard & tools
├── shared/                  # Common utilities, helpers
└── static/                  # CSS, images, minimal JS
```

### 5.3 Key Integrations

#### Crypto Payments
- Integration point: Payment gateway (BTCPay, Coinbase, or similar)
- Flow: Provider selects crypto → receives payment address → payment verification webhook
- Verification: Manual confirmation in admin dashboard for MVP
- Reconciliation: Monthly manual reconciliation against subscription database

#### Email System
- Transactional: Sign-up confirmations, password resets, subscription renewals
- Marketing: Monthly newsletter (optional for MVP)
- Service: SendGrid, AWS SES, or Mailgun

#### Map/Location Data
- Location filtering: Hardcoded or CSV-based country/city list (MVP)
- Future: Integration with Google Maps or Mapbox (out of scope)

### 5.4 Security Considerations

- HTTPS/TLS for all communications
- Password hashing: bcrypt or Argon2
- CSRF protection for forms
- Rate limiting on login/payment endpoints
- Bank account details: Encrypted at rest
- Crypto addresses: Read-only, provider-submitted
- PCI compliance: Avoid storing payment card data (use payment processor)
- Admin authentication: Strong passwords + optional 2FA

### 5.5 Database Schema (High-Level)

```
Users
  ├── id, email, password_hash, created_at
  ├── type (provider/client/admin)

Providers
  ├── user_id, name, phone, bio, photo_url, created_at
  ├── subscription_status (active/inactive/suspended)
  ├── subscription_payment_method (crypto/bank_transfer)
  ├── crypto_address (optional)
  ├── bank_account_details_encrypted (optional)

Services
  ├── id, provider_id, type, description, price, duration

Certifications
  ├── id, provider_id, name, image_url

Reviews
  ├── id, provider_id, client_name, rating, comment, created_at

SubscriptionPayments
  ├── id, provider_id, amount, status, payment_method, reference, created_at

AdminAuditLog
  ├── id, admin_id, action, target, created_at
```

### 5.6 API Endpoints (Server-Side Rendering - Minimal APIs)

Most operations are form-based HTML submissions. Limited APIs for:
- `/api/providers/search` (JSON for filtering)
- `/api/reviews/submit` (form submission)
- `/api/auth/logout` (POST)

---

## 6. Success Metrics

### Early Indicators (Month 1-2)
- **Provider Onboarding:** 10+ providers sign up
- **Listings Created:** 30+ service listings published
- **Payment Methods:** At least 50% of providers select crypto payment option
- **Site Performance:** <2s page load time (p95)
- **Uptime:** 99.5% availability

### Growth Indicators (Month 3)
- **Active Providers:** 50+ providers with active subscriptions
- **Client Engagement:** 500+ unique monthly visitors
- **Reviews:** 20+ reviews submitted with >4.0 average rating
- **Payment Success:** 95% of crypto/bank transfer payments succeed
- **Revenue:** Predictable monthly subscription revenue from active providers

### Health Metrics (Ongoing)
- **Churn Rate:** <10% monthly provider churn
- **Support Requests:** <1% of providers require admin intervention
- **Content Quality:** <2% of listings/reviews flagged for removal
- **Mobile Traffic:** >60% of client traffic from mobile
- **Conversion:** Visit-to-review ratio >5%

---

## 7. Three-Month Timeline

### Phase 1: Foundation (Weeks 1-4)

**Goal:** Core infrastructure and basic provider portal

- Week 1-2: Project setup, tech stack selection, database design
  - [ ] Infrastructure provisioning (hosting, database, payment processor account)
  - [ ] Authentication system (signup, login, email verification)
  - [ ] Basic provider profile model
  
- Week 3-4: Provider portal foundation
  - [ ] Provider signup flow
  - [ ] Profile creation and editing
  - [ ] Service listing CRUD operations
  - [ ] Basic profile view page

**Deliverables:** Provider portal with working account creation and service management

### Phase 2: Marketplace & Payments (Weeks 5-8)

**Goal:** Client browsing, search/filtering, and payment integration

- Week 5: Client marketplace
  - [ ] Provider directory page
  - [ ] Service type and location dropdowns
  - [ ] Provider profile view pages
  - [ ] Price range filtering
  
- Week 6: Search & filtering
  - [ ] Combined search/filter logic
  - [ ] Database query optimization
  - [ ] URL-based filter persistence
  
- Week 7: Payment integration
  - [ ] Crypto payment processor setup (BTCPay/Coinbase)
  - [ ] Payment method selection in provider portal
  - [ ] Bank transfer form for manual processing
  - [ ] Payment verification endpoint
  
- Week 8: Reviews system
  - [ ] Review submission form
  - [ ] Review display on provider profiles
  - [ ] Rating calculation and display
  - [ ] Basic review moderation

**Deliverables:** Full marketplace with search/filter, payment methods integrated, reviews functional

### Phase 3: Admin & Polish (Weeks 9-12)

**Goal:** Admin dashboard, payment verification workflow, and MVP launch readiness

- Week 9: Admin dashboard
  - [ ] Admin authentication and role management
  - [ ] Provider management interface
  - [ ] Subscription status tracking
  - [ ] Basic analytics dashboard
  
- Week 10: Payment operations
  - [ ] Bank transfer verification workflow
  - [ ] Payment history and receipts
  - [ ] Subscription renewal tracking
  - [ ] Manual payment processing UI
  
- Week 11: Quality assurance & optimization
  - [ ] Security audit (HTTPS, CSRF, rate limiting)
  - [ ] Performance testing and optimization
  - [ ] Mobile responsiveness verification
  - [ ] Cross-browser testing
  - [ ] Documentation (API, deployment, operations)
  
- Week 12: Launch preparation & soft launch
  - [ ] Onboard first 5-10 beta providers
  - [ ] Monitor payments and system stability
  - [ ] Gather feedback and fix critical bugs
  - [ ] Final security checks
  - [ ] Public launch

**Deliverables:** Full MVP product ready for public launch with operational admin dashboard

### Parallel Track (Ongoing)
- Crypto payment monitoring and integration adjustments
- Email template creation (signup, payment confirmation, renewal notices)
- Terms of Service and Privacy Policy drafting
- Basic content moderation guidelines
- Monitoring and alerting setup

### Post-Launch (Week 13+)
- Monitoring system stability and payment processing
- Rapid iteration based on user feedback
- Scale infrastructure as needed
- Plan Phase 2 features (in-app messaging, advanced analytics, mobile app)

---

## 8. Out of Scope (Post-MVP)

The following features are intentionally excluded from MVP to accelerate time-to-market:

- **In-app Messaging:** Clients contact providers directly via phone/email instead
- **Advanced Analytics:** Only basic metrics in MVP; detailed dashboards for Phase 2
- **Mobile-Specific App:** Responsive web design covers mobile needs
- **Complex Verification:** No background checks or advanced provider vetting in MVP
- **Automated Payment Renewals:** Manual admin processing of subscription renewals
- **Multi-language Support:** English-only MVP
- **Multiple Subscription Tiers:** Single tier MVP; tiered options in Phase 2
- **Provider Ratings Algorithm:** Simple average rating; ML-based recommendations later
- **Dispute Resolution System:** Manual admin handling; formal arbitration system in Phase 2
- **Integration with Booking Systems:** Manual booking via contact details (no calendar sync)
- **Advanced Search (AI/ML):** Basic filters sufficient for MVP scale
- **Service Bundles/Packages:** Individual services only

---

## 9. Appendix

### A. Glossary

- **MVP:** Minimum Viable Product - the smallest set of features needed to launch
- **Subscription:** Monthly recurring charge to providers for marketplace access
- **Provider:** Massage therapist or service professional offering services
- **Client:** End user browsing and booking services
- **Listing:** A specific service offered by a provider
- **Crypto Address:** Blockchain wallet address for receiving payments
- **Bank Transfer:** Direct fund transfer from provider's bank account

### B. Success Criteria for Launch

- [ ] All Phase 1, 2, and 3 deliverables complete
- [ ] At least 10 providers successfully signed up and listed services
- [ ] All payment methods (crypto and bank transfer) tested and functional
- [ ] Admin dashboard fully operational
- [ ] Security audit passed
- [ ] Performance targets met (<2s load time)
- [ ] Legal documents (ToS, Privacy Policy) approved
- [ ] Team trained on support and payment processing
- [ ] Monitoring and alerting in place

### C. Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Crypto integration delays | Use managed payment processor; fallback to crypto-only for beta |
| Payment processing failures | Implement manual verification workflow; clear communication with providers |
| Regulatory compliance | Consult with legal team on jurisdiction; limit to compliant regions initially |
| Low provider adoption | Launch with pre-recruited providers; partner with massage associations |
| Security vulnerabilities | Regular security audits; bug bounty program post-launch |
| Technical debt accumulation | Code review process; prioritize refactoring in Phase 2 |

---

**Document Status:** Ready for Development  
**Next Steps:** Tech stack selection, team allocation, sprint planning
