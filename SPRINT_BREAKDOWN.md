# Massage Marketplace - Detailed Sprint Breakdown
## 12-Week Development Plan (3 Sprints × 4 Weeks)

**Infrastructure Note:** Provisioning, deployment, and monitoring setup deferred to Week 11 (pre-launch)

---

## SPRINT 1: Foundation & Provider Portal (Weeks 1-4)

### Goal
Working provider signup, profile management, and service listings with Django admin operational.

### Week 1: Project Bootstrap & Database Schema

**Sprint Planning (Day 1):**
- [ ] Team kickoff meeting (15 min)
- [ ] Review PRD and technical decisions
- [ ] Assign roles (backend lead, frontend lead, DevOps for later)
- [ ] Setup shared docs/Slack channel

**Development (Days 1-5):**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Initialize Django 5.0 project | Backend Lead | 2 |
| Create `users`, `providers`, `reviews`, `payments` apps | Backend Lead | 2 |
| Define User model (custom, extends AbstractUser) | Backend Lead | 3 |
| Define Provider model (profile, subscriptions, certifications) | Backend Lead | 4 |
| Define Service model | Backend Lead | 2 |
| Define Certification model (image uploads) | Backend Lead | 2 |
| Define Review model | Backend Lead | 2 |
| Define SubscriptionPayment model | Backend Lead | 2 |
| Database migrations | Backend Lead | 1 |
| Setup Django admin for all models | Backend Lead | 3 |
| Git repo setup + initial commit | Backend Lead | 1 |
| Local development README | Backend Lead | 1 |
| **Total** | | **25 hours** |

**Deliverables:**
- [ ] Django project with all core models
- [ ] Django admin registered and tested
- [ ] Git repo with clean initial commit
- [ ] Development environment runnable locally for all team members
- [ ] Database schema documented

**Definition of Done:**
```bash
$ python manage.py runserver
# Admin at http://localhost:8000/admin
# Can CRUD all models in Django admin
```

---

### Week 2: Authentication & Provider Signup Flow

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Create AuthenticationBackend (email-based login) | Backend Lead | 3 |
| Implement signup view (Provider) | Backend Lead | 4 |
| Email verification flow (token-based) | Backend Lead | 4 |
| Password reset view | Backend Lead | 3 |
| Login/logout views | Backend Lead | 2 |
| Create base templates (layout, nav) | Frontend Lead | 3 |
| Create signup form template | Frontend Lead | 2 |
| Create login template | Frontend Lead | 1 |
| Create email templates (verification, reset) | Frontend Lead | 2 |
| Form validation (frontend + backend) | Backend Lead | 3 |
| Session management + redirects | Backend Lead | 2 |
| User model tests | Backend Lead | 2 |
| **Total** | | **31 hours** |

**Deliverables:**
- [ ] Provider signup flow complete
- [ ] Email verification working (console output in dev)
- [ ] Login/logout working
- [ ] Session persistence
- [ ] Password reset flow functional

**Definition of Done:**
```
1. Navigate to /signup
2. Enter email, password → receive verification email (console)
3. Click verification link → account activated
4. Login with email/password
5. Dashboard redirects to /provider/dashboard (to be built)
```

---

### Week 3: Provider Profile & Service Management

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Create Provider profile model fields | Backend Lead | 1 |
| Build provider profile update view | Backend Lead | 3 |
| Profile form with file upload (photo) | Frontend Lead | 4 |
| Certification upload (multiple images) | Frontend Lead | 3 |
| Provider dashboard template | Frontend Lead | 2 |
| Service CRUD views (create, read, update, delete) | Backend Lead | 5 |
| Service form template + validation | Frontend Lead | 3 |
| Service listing display on provider dashboard | Frontend Lead | 2 |
| Photo/certification storage (local filesystem for MVP) | Backend Lead | 2 |
| Image validation (size, format) | Backend Lead | 2 |
| URL routing for all provider views | Backend Lead | 2 |
| Provider view tests | Backend Lead | 2 |
| **Total** | | **31 hours** |

**Deliverables:**
- [ ] Complete profile edit page (name, bio, phone, photo)
- [ ] Certification upload and display
- [ ] Service CRUD fully functional
- [ ] Provider dashboard showing profile + services
- [ ] Image uploads working locally

**Definition of Done:**
```
1. Signup → Profile page loads
2. Fill profile (name, bio, phone, photo) → Save
3. View saved profile
4. Create service (type, price, duration) → Listed on dashboard
5. Edit/delete service works
```

---

### Week 4: Django Admin Extensions & Subscription Basics

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Extend Django admin with custom filters | Backend Lead | 3 |
| Add Provider admin view (list, search, filter by status) | Backend Lead | 2 |
| Add Service admin view with inline editing | Backend Lead | 2 |
| Add SubscriptionPayment admin view | Backend Lead | 2 |
| Create provider list view (internal - no filters yet) | Frontend Lead | 2 |
| Implement subscription_status field logic | Backend Lead | 2 |
| Create subscription payment form skeleton | Frontend Lead | 2 |
| Add payment method selection (crypto/bank - UI only) | Frontend Lead | 2 |
| Basic provider settings/subscription page | Frontend Lead | 2 |
| Refactor templates (DRY, consistent styling) | Frontend Lead | 3 |
| End-to-end test: signup → profile → service → payment page | QA/Backend Lead | 2 |
| Update development README with test providers | Backend Lead | 1 |
| Sprint retrospective & documentation | Team | 2 |
| **Total** | | **27 hours** |

**Deliverables:**
- [ ] Django admin fully configured for daily operations
- [ ] Provider subscription settings page (UI only, no backend logic yet)
- [ ] Test providers created in admin
- [ ] Complete provider flow (signup to services to subscription page)
- [ ] Sprint documentation

**Definition of Done:**
```
Sprint 1 complete:
- Admin can manage all providers, services, payments
- Provider can: signup → profile → create services → see subscription page
- All core models working and tested
- Ready for marketplace client development
```

**Sprint 1 Retro Tasks:**
- Code review all templates for consistency
- Update CONTRIBUTING.md
- Document API (even though server-rendered, useful for future)

---

## SPRINT 2: Marketplace & Core Features (Weeks 5-8)

### Goal
Working client marketplace with search/filter, provider profiles, reviews, and payment forms ready.

### Week 5: Client Marketplace - Provider Directory

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Create public provider list view (no auth required) | Backend Lead | 3 |
| Provider card component (Tailwind) | Frontend Lead | 2 |
| Provider detail page (public profile view) | Backend Lead | 2 |
| Provider detail template (services, photo, certifications) | Frontend Lead | 3 |
| Display average rating on provider cards | Backend Lead | 2 |
| Display service listings on provider detail | Frontend Lead | 1 |
| Pagination for provider list (50 per page) | Backend Lead | 2 |
| Database query optimization (select_related, prefetch_related) | Backend Lead | 2 |
| Basic breadcrumb navigation | Frontend Lead | 1 |
| Mobile responsiveness check | Frontend Lead | 2 |
| View tests (provider list, detail) | Backend Lead | 3 |
| **Total** | | **23 hours** |

**Deliverables:**
- [ ] Public provider directory page (/)
- [ ] Provider detail pages (/:id)
- [ ] Pagination working
- [ ] Mobile responsive
- [ ] All views tested

**Definition of Done:**
```
1. Visit / (not logged in)
2. See list of providers with photos, names, ratings
3. Click provider → see full profile, services, certifications
4. Pagination works (50 per page)
5. Mobile view works
```

---

### Week 6: Search & Filtering

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Create service type choices (enum in model) | Backend Lead | 1 |
| Create location data (country, city lists - CSV or hardcoded) | Backend Lead | 2 |
| Build service type filter | Backend Lead | 2 |
| Build location (country) filter | Backend Lead | 2 |
| Build location (city) filter (dynamic per country) | Backend Lead | 3 |
| Build price range filter (slider) | Frontend Lead | 3 |
| Combine filters (multi-field search) | Backend Lead | 4 |
| Preserve filter state in URL query params | Backend Lead | 2 |
| Filter form template (clean UI) | Frontend Lead | 2 |
| Real-time filter results (form submission, not AJAX) | Frontend Lead | 2 |
| Add "reset filters" button | Frontend Lead | 1 |
| Database indexes for filtering (service_type, country, city) | Backend Lead | 1 |
| Query optimization for filtered results | Backend Lead | 2 |
| Filter tests (all combinations) | Backend Lead | 3 |
| **Total** | | **30 hours** |

**Deliverables:**
- [ ] All filters working (service type, country, city, price)
- [ ] Combined filtering working
- [ ] URL query strings preserving state
- [ ] Clean, accessible filter UI
- [ ] Optimized database queries

**Definition of Done:**
```
1. Visit / with filters
2. Filter by: Service Type=Swedish, Country=USA, City=NYC, Price=50-100
3. Results update
4. URL shows: /?service_type=swedish&country=usa&city=nyc&price_min=50&price_max=100
5. Share URL → same results load for others
6. Click reset → all filters cleared
```

---

### Week 7: Reviews System

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Create review submission form (5-star + comment) | Frontend Lead | 2 |
| Review submission view (POST handler) | Backend Lead | 3 |
| Basic validation (1-5 stars, 250 char max comment) | Backend Lead | 2 |
| Calculate average provider rating | Backend Lead | 2 |
| Display reviews on provider detail page | Frontend Lead | 2 |
| Review list (newest first) | Frontend Lead | 2 |
| Display reviewer name (optional) and date | Frontend Lead | 1 |
| Star rating display (read-only) | Frontend Lead | 1 |
| Simple spam prevention (1 review per provider per client max - enforce via DB unique constraint) | Backend Lead | 2 |
| Admin moderation: flag/approve reviews | Backend Lead | 2 |
| Email notification on new review (admin) | Backend Lead | 2 |
| Review tests (submission, display, validation) | Backend Lead | 3 |
| **Total** | | **24 hours** |

**Deliverables:**
- [ ] Review submission form functional
- [ ] Reviews displayed on provider profiles
- [ ] Average rating calculated and displayed
- [ ] Admin can moderate reviews
- [ ] Email notifications working

**Definition of Done:**
```
1. On provider detail page, see review form
2. Submit: 5 stars + "Great massage!" 
3. Review appears on profile immediately
4. Average rating updates
5. Admin receives notification email
```

---

### Week 8: Payment Substrate & Crypto Form

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Update SubscriptionPayment model with all fields | Backend Lead | 1 |
| Create subscription settings page view | Backend Lead | 2 |
| Payment method selection form (radio: crypto/bank) | Frontend Lead | 2 |
| Crypto payment form (address entry, read-only display) | Frontend Lead | 2 |
| Bank transfer payment form (bank details, encrypted storage) | Frontend Lead | 3 |
| Form validation (address format, bank fields required) | Backend Lead | 3 |
| Display current subscription status and renewal date | Frontend Lead | 2 |
| Subscription status logic (active/inactive/expired) | Backend Lead | 3 |
| Generate wallet address display for crypto (display provider's address) | Frontend Lead | 1 |
| Implement subscribe/unsubscribe toggle | Backend Lead | 2 |
| Store subscription renewal date (monthly from today) | Backend Lead | 2 |
| Email confirmation on subscription | Backend Lead | 2 |
| Admin view: payment processing queue | Frontend Lead | 2 |
| Payment flow tests | Backend Lead | 3 |
| **Total** | | **30 hours** |

**Deliverables:**
- [ ] Provider subscription management page complete
- [ ] Payment method selection (crypto/bank)
- [ ] Subscription status tracking
- [ ] Subscription/unsubscribe flow working
- [ ] Forms validated and secure

**Definition of Done:**
```
1. After signup, provider goes to /provider/subscription
2. See current status (inactive)
3. Choose payment method: crypto or bank
4. If crypto: see wallet address to send payment to
5. If bank: enter bank details → stored encrypted
6. Click "Subscribe" → marked as active, renewal date set to 30 days
7. Toggle to inactive pauses listing
```

**Sprint 2 Retro Tasks:**
- Performance testing (query counts, page load times)
- Accessibility audit (WCAG)
- Update README with marketplace URLs

---

## SPRINT 3: Admin Dashboard, Payments, & Launch Prep (Weeks 9-12)

### Goal
Complete admin dashboard, crypto payment monitoring, final polish, and production readiness.

### Week 9: Admin Dashboard

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Create admin dashboard landing page | Frontend Lead | 2 |
| Admin provider management view (list, search, filter) | Backend Lead | 3 |
| Admin provider detail view (edit, suspend, view stats) | Backend Lead | 2 |
| Admin subscription status overview (active/inactive counts) | Frontend Lead | 2 |
| Admin audit log (track all changes) | Backend Lead | 3 |
| Analytics dashboard (provider count, revenue, reviews) | Frontend Lead | 2 |
| Payment status overview (pending, completed, failed) | Frontend Lead | 2 |
| Admin user management (create/remove admin accounts) | Backend Lead | 2 |
| Role-based access (admin vs support staff) | Backend Lead | 2 |
| Admin authentication + password reset | Backend Lead | 2 |
| Extend Django admin for quick actions | Backend Lead | 2 |
| Dashboard tests | Backend Lead | 2 |
| **Total** | | **26 hours** |

**Deliverables:**
- [ ] Admin dashboard fully functional
- [ ] Provider management operational
- [ ] Basic analytics visible
- [ ] Audit logging working
- [ ] Role-based access implemented

**Definition of Done:**
```
Admin can:
1. View all providers (search, filter by status)
2. See subscription status overview
3. View analytics (total providers, listings, avg rating, revenue)
4. Access provider details and manage subscriptions
5. See audit log of all changes
```

---

### Week 10: Crypto Payment Monitoring & Bank Verification Workflow

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Setup web3.py library and configuration | Backend Lead | 2 |
| Create Bitcoin wallet monitoring (Blockchain.com API - free) | Backend Lead | 4 |
| Create Ethereum wallet monitoring (Etherscan API - free) | Backend Lead | 4 |
| Create USDC wallet monitoring (via Etherscan) | Backend Lead | 3 |
| Implement cron job (check wallets every hour) | Backend Lead | 3 |
| Match payment to provider (address lookup in DB) | Backend Lead | 2 |
| Update subscription status on payment detection | Backend Lead | 2 |
| Log payment confirmations in SubscriptionPayment model | Backend Lead | 2 |
| Email confirmation to provider (payment received) | Backend Lead | 2 |
| Bank transfer verification workflow view | Frontend Lead | 2 |
| Admin payment approval/rejection form | Frontend Lead | 2 |
| Payment confirmation email to provider | Backend Lead | 1 |
| Dispute/failed payment handling (mark as failed, notify provider) | Backend Lead | 3 |
| Payment monitoring tests | Backend Lead | 3 |
| **Total** | | **35 hours** |

**Deliverables:**
- [ ] Crypto payment monitoring working
- [ ] Bank transfer verification workflow operational
- [ ] Payment confirmations sent
- [ ] All payment flows tested
- [ ] Admin can verify/reject payments

**Definition of Done:**
```
Crypto flow:
1. Provider submits address in settings
2. Cron job detects payment in 1 hour (test with testnet)
3. Subscription marked as active
4. Provider receives confirmation email

Bank flow:
1. Provider submits bank details
2. Admin sees in payment queue
3. Admin verifies (checks bank, approves)
4. Subscription marked active
5. Provider receives confirmation email
```

---

### Week 11: Security, Performance & Infrastructure Setup

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Security audit (CSRF tokens, XSS prevention, SQL injection) | Backend Lead | 4 |
| HTTPS/SSL preparation (Let's Encrypt certificates, nginx config) | DevOps/Backend Lead | 3 |
| Rate limiting (login, API endpoints) | Backend Lead | 2 |
| Password hashing verification (bcrypt/Argon2) | Backend Lead | 1 |
| CORS headers (if needed for future APIs) | Backend Lead | 1 |
| Environment variables setup (.env handling) | Backend Lead | 1 |
| Secrets management (database password, API keys) | Backend Lead | 1 |
| Performance profiling (query count, page load times) | Backend Lead | 2 |
| Database indexing (full optimization) | Backend Lead | 2 |
| Caching strategy (if needed) | Backend Lead | 1 |
| Setup error logging (Sentry or similar) | Backend Lead | 2 |
| Setup monitoring/alerting for uptime | DevOps | 2 |
| Provision VPS (DigitalOcean/Linode) | DevOps | 2 |
| Install & configure PostgreSQL on VPS | DevOps | 2 |
| Install & configure Minio (S3 alternative) | DevOps | 2 |
| Install & configure Nginx + Gunicorn | DevOps | 2 |
| Setup systemd services | DevOps | 2 |
| Domain setup & DNS | DevOps | 1 |
| SSL certificate setup (Let's Encrypt) | DevOps | 1 |
| Database migration to production | Backend Lead | 2 |
| Static file collection (CSS, images) | Backend Lead | 1 |
| Load balancer setup (if needed, probably not for MVP) | DevOps | 0 |
| Backup strategy (database, files) | DevOps | 2 |
| **Total** | | **40 hours** |

**Deliverables:**
- [ ] Security audit passed
- [ ] VPS provisioned and configured
- [ ] Database, Minio, Nginx, Gunicorn running
- [ ] SSL certificates installed
- [ ] Monitoring and logging operational
- [ ] Backup strategy documented

**Definition of Done:**
```
1. App running on VPS at https://yourdomain.com
2. All pages load <2 seconds (p95)
3. SSL certificate valid
4. Monitoring alerts on errors/downtime
5. Database backups running daily
6. Security checklist passed
```

---

### Week 12: Beta Testing, Launch Prep & Go Live

**Development:**

| Task | Owner | Est. Hours |
|------|-------|-----------|
| Create Terms of Service document | Legal/Product | 3 |
| Create Privacy Policy document | Legal/Product | 3 |
| Create payment policy (crypto/bank terms) | Legal/Product | 2 |
| Onboard 5-10 beta providers (manual) | Product/Support | 3 |
| Test full flow: signup → profile → service → payment → review | QA | 4 |
| Test payment flows (crypto testnet, bank simulated) | QA | 3 |
| Test on mobile browsers (iOS Safari, Chrome Mobile) | QA | 2 |
| Test on desktop browsers (Chrome, Firefox, Safari, Edge) | QA | 2 |
| End-to-end test with real beta providers | Product | 4 |
| Load testing (simulate 100+ concurrent users) | Backend Lead | 2 |
| Fix any critical bugs found | Backend Lead + Frontend Lead | 5 |
| Update README with deployment instructions | Backend Lead | 2 |
| Create operations runbook (common tasks, troubleshooting) | DevOps | 2 |
| Create support documentation for admin team | Product/Support | 2 |
| Soft launch (announce to beta providers) | Product | 1 |
| Monitor production 24/7 for issues | Team | 8 |
| Fix post-launch bugs (rapid iteration) | Backend Lead + Frontend Lead | 5 |
| **Total** | | **53 hours** |

**Deliverables:**
- [ ] Legal documents finalized and hosted
- [ ] 5+ beta providers onboarded and tested
- [ ] All user flows tested end-to-end
- [ ] Mobile and desktop testing complete
- [ ] Operations documentation ready
- [ ] Public launch announced

**Definition of Done:**
```
Launch complete:
1. https://yourdomain.com live and public
2. Terms of Service, Privacy Policy, Payment Policy live
3. 5+ providers successfully subscribed (at least 1 via crypto, 1 via bank)
4. At least 3 reviews posted
5. Admin dashboard operational
6. All monitoring alerts configured
7. Support team trained
```

**Post-Launch (Week 13+):**
- Monitor payments and system stability
- Rapid iteration on user feedback
- Scale infrastructure as needed
- Plan Phase 2 features

---

## Sprint Summary

| Sprint | Focus | Weeks | Hours |
|--------|-------|-------|-------|
| 1 | Foundation & Provider Portal | 1-4 | 116 |
| 2 | Marketplace & Features | 5-8 | 107 |
| 3 | Admin, Payments, Launch | 9-12 | 128 |
| **Total** | | **12** | **351** |

**Team Capacity per Week:** ~40 hours (2-3 developers)  
**Recommended:** 3 developers (1 backend lead, 1 frontend lead, 1 DevOps/QA)

---

## Daily Standup Format

**Every morning (10 min):**
1. What did you complete yesterday?
2. What are you working on today?
3. Any blockers?

---

## Definition of Done (All Work)

Before marking task complete:
- [ ] Code written and committed to Git
- [ ] Tests written (unit or integration)
- [ ] Code reviewed by 1+ peer
- [ ] Deployed to dev environment
- [ ] Tested in browser (if frontend)
- [ ] No console errors/warnings
- [ ] Documented (if needed)

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|-----------|
| Crypto integration complex | 2-3 | Use public APIs (Blockchain.com, Etherscan) instead of private nodes |
| Payment verification errors | 3 | Manual admin verification workflow as fallback |
| Database migration issues | 3 | Test migration script multiple times before prod |
| Late-stage bugs | 3 | Reserve 2-3 days in week 12 for buffer |
| Team availability | All | Document as you go; pair program on critical tasks |

---

## Success Criteria per Sprint

**Sprint 1:** Provider can signup, create profile and services  
**Sprint 2:** Client can browse, search, filter, and review providers  
**Sprint 3:** Payments working, admin dashboard operational, live on production

