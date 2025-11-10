# Power Automate Cost Estimate for CR Reminder Flows

## Executive Summary

**Total Monthly Cost**: **$15 USD** (Power Automate per-user plan)

This covers unlimited runs for all three reminder flows with premium connectors (Azure DevOps, Azure AD, SharePoint).

---

## Licensing Model

### Power Automate Per-User Plan
- **Cost**: $15 USD/month per user
- **Includes**:
  - Unlimited flow runs
  - All premium connectors (Azure DevOps, Azure AD, HTTP, etc.)
  - 50 MB database capacity (Dataverse)
  - 250 MB file capacity
  - 10,000 API requests/day per user

### What's Covered
✅ Azure DevOps connector (premium)  
✅ Azure AD connector (premium)  
✅ SharePoint connector (standard)  
✅ Office 365 Outlook connector (standard)  
✅ Unlimited flow executions  
✅ All three reminder flows

### Alternative: Per-Flow Plan
- **Cost**: $100 USD/month per flow
- **Use case**: If flows need to run under multiple user contexts
- **Total for 3 flows**: $300 USD/month
- **Not recommended** for this scenario (single service account is sufficient)

---

## Usage Projections

### Assumptions
Based on your Azure DevOps data:
- **Total CRs**: 25,076
- **Active CRs** (Approved, In Progress, Awaiting PIR): ~500 (estimated 2%)
- **Distribution**:
  - Approved: ~100 CRs
  - In Progress: ~200 CRs
  - Awaiting PIR: ~200 CRs

### Flow A - Approved State Reminders

**Recurrence**: Every 10 minutes = 144 runs/day

| Metric | Value |
|--------|-------|
| Runs per day | 144 |
| Runs per month | 4,320 |
| Avg CRs per run | 5-10 (within 30-min window) |
| API calls per run | 3-5 (WIQL + batch + logging) |
| Total API calls/month | ~17,280 |
| Emails sent/month | ~300 (2 per CR: pre-start + follow-up) |

**Cost**: Included in $15/month license

---

### Flow B - In Progress State Reminders

**Recurrence**: Every 10 minutes = 144 runs/day

| Metric | Value |
|--------|-------|
| Runs per day | 144 |
| Runs per month | 4,320 |
| Avg CRs per run | 10-15 (within 30-min window) |
| API calls per run | 3-6 (WIQL + batch + manager lookup + logging) |
| Total API calls/month | ~21,600 |
| Emails sent/month | ~400 (pre-end + inquiries) |
| Escalations/month | ~20 (5% of inquiries) |

**Cost**: Included in $15/month license

---

### Flow C - Awaiting PIR State Reminders

**Recurrence**: Every 4 hours = 6 runs/day

| Metric | Value |
|--------|-------|
| Runs per day | 6 |
| Runs per month | 180 |
| Avg CRs per run | 200 (all awaiting PIR) |
| API calls per run | 3-4 (WIQL + batch + logging) |
| Total API calls/month | ~720 |
| Emails sent/month | ~600 (3 reminders per CR over 30 days) |
| Escalations/month | ~40 (20% of CRs) |

**Cost**: Included in $15/month license

---

## Total Monthly Usage

| Resource | Usage | Limit | Status |
|----------|-------|-------|--------|
| **Flow runs** | ~8,820 | Unlimited | ✅ Well within |
| **API calls** | ~39,600 | 300,000/month | ✅ 13% utilized |
| **Emails sent** | ~1,300 | Unlimited | ✅ No limit |
| **SharePoint items** | ~1,300/month | Unlimited | ✅ No limit |
| **Storage** | <1 MB | 50 MB | ✅ Minimal |

**Conclusion**: Single per-user license is more than sufficient.

---

## Cost Breakdown by Component

### Monthly Costs

| Component | Cost | Notes |
|-----------|------|-------|
| Power Automate per-user | $15.00 | Service account license |
| Azure DevOps API | $0.00 | Included in TFS license |
| SharePoint storage | $0.00 | Included in Microsoft 365 |
| Email delivery | $0.00 | Included in Exchange Online |
| Azure AD lookups | $0.00 | Included in Azure AD license |
| **Total** | **$15.00** | |

### Annual Cost
- **$15 × 12 = $180 USD/year**

---

## Scaling Considerations

### If CR Volume Doubles (50,000 CRs, 1,000 active)

| Metric | Current | Doubled | Impact |
|--------|---------|---------|--------|
| Flow runs/month | 8,820 | 8,820 | No change (time-based) |
| API calls/month | 39,600 | 79,200 | Still 26% of limit |
| Emails/month | 1,300 | 2,600 | No cost impact |
| Cost | $15 | $15 | **No change** |

**Conclusion**: Current license scales to 2-3x volume with no additional cost.

### If CR Volume 10x (250,000 CRs, 5,000 active)

| Metric | Current | 10x | Impact |
|--------|---------|-----|--------|
| API calls/month | 39,600 | 396,000 | Exceeds 300K limit |
| Recommendation | Single license | **Add 1 more license** | $30/month |

**Conclusion**: Would need second license only at 10x current volume.

---

## Cost Comparison: Alternative Approaches

### Option 1: Current Approach (Direct API)
- **Cost**: $15/month
- **Pros**: Real-time data, no sync lag, simple architecture
- **Cons**: API rate limits, more complex flows

### Option 2: Database-Driven (with sync)
- **Cost**: $15/month (same license) + SQL Server costs (existing)
- **Pros**: No API rate limits, faster queries, pre-filtered data
- **Cons**: Sync lag, additional sync flow, data staleness

### Option 3: Hybrid (API + Cache)
- **Cost**: $15/month + minimal Azure Table Storage (~$1/month)
- **Pros**: Best of both worlds, reduced API calls
- **Cons**: More complex, cache invalidation logic

**Recommendation**: Stick with Option 1 (Direct API) - simplest and most cost-effective.

---

## ROI Analysis

### Manual Process Cost (Before Automation)

Assumptions:
- **Time per manual reminder**: 5 minutes
- **Reminders per month**: 1,300
- **Total manual time**: 108 hours/month
- **Hourly rate**: $50 (average IT staff)
- **Monthly manual cost**: $5,400

### Automated Process Cost
- **License**: $15/month
- **Setup time**: 40 hours (one-time)
- **Maintenance**: 2 hours/month
- **Monthly cost**: $15 + (2 × $50) = $115

### Savings
- **Monthly savings**: $5,400 - $115 = **$5,285**
- **Annual savings**: **$63,420**
- **Payback period**: < 1 week

### Additional Benefits (Not Quantified)
- ✅ 100% consistency (no missed reminders)
- ✅ Audit trail (all reminders logged)
- ✅ Faster escalation (automated)
- ✅ Better compliance
- ✅ Reduced human error
- ✅ Staff can focus on higher-value work

---

## Budget Planning

### Year 1 Costs

| Item | Cost | Notes |
|------|------|-------|
| Power Automate license | $180 | 12 months |
| Setup/development | $2,000 | 40 hours @ $50/hr |
| Testing | $500 | 10 hours @ $50/hr |
| Documentation | $250 | 5 hours @ $50/hr |
| Training | $250 | 5 hours @ $50/hr |
| **Total Year 1** | **$3,180** | |

### Year 2+ Costs

| Item | Cost | Notes |
|------|------|-------|
| Power Automate license | $180 | 12 months |
| Maintenance | $1,200 | 2 hrs/month @ $50/hr |
| Updates/enhancements | $500 | Ad-hoc |
| **Total Year 2+** | **$1,880** | |

### 3-Year Total Cost of Ownership
- **Year 1**: $3,180
- **Year 2**: $1,880
- **Year 3**: $1,880
- **Total**: $6,940

### 3-Year Savings (vs. Manual)
- **Manual cost**: $194,400 (3 × $64,800)
- **Automated cost**: $6,940
- **Net savings**: **$187,460**
- **ROI**: **2,700%**

---

## Risk Mitigation

### API Rate Limit Risk
- **Limit**: 60 requests/minute per PAT
- **Current usage**: ~27 requests/minute (worst case)
- **Mitigation**: 
  - Stagger flow schedules
  - Implement retry with backoff
  - Monitor usage in Application Insights
- **Cost impact**: None (within limits)

### License Interruption Risk
- **Risk**: Service account license expires
- **Impact**: All flows stop
- **Mitigation**:
  - Set up license expiration alerts
  - Document renewal process
  - Have backup PAT ready
- **Cost impact**: None (preventable)

### Volume Spike Risk
- **Risk**: Sudden increase in CR volume
- **Impact**: More API calls, potential rate limiting
- **Mitigation**:
  - Monitor API usage trends
  - Adjust flow frequency if needed
  - Consider second license if sustained 10x growth
- **Cost impact**: $15/month for second license (only if needed)

---

## Recommendations

### Immediate (Month 1)
1. ✅ Purchase single Power Automate per-user license ($15/month)
2. ✅ Set up service account with license
3. ✅ Implement Flow A (Approved reminders)
4. ✅ Test with small CR set
5. ✅ Monitor API usage and flow performance

### Short-term (Months 2-3)
1. ✅ Implement Flow B (In Progress reminders)
2. ✅ Implement Flow C (Awaiting PIR reminders)
3. ✅ Set up monitoring and alerting
4. ✅ Document processes and runbooks
5. ✅ Train CAB team on flow management

### Long-term (Months 4-12)
1. ✅ Optimize based on usage patterns
2. ✅ Add advanced features (adaptive cards, Teams integration)
3. ✅ Expand to other change types if successful
4. ✅ Consider Power BI dashboards for analytics
5. ✅ Review and renew license annually

### Future Enhancements (Optional)
- **Adaptive Cards**: Interactive reminders in Teams ($0 - included)
- **Power BI**: Visual dashboards ($10/user/month - optional)
- **Power Apps**: Custom CR submission form ($5/user/month - optional)
- **Application Insights**: Advanced monitoring ($0 - free tier sufficient)

**Total enhanced cost**: $15-30/month (depending on optional features)

---

## Conclusion

**The Power Automate reminder flows are highly cost-effective:**

- ✅ **Low cost**: $15/month (or $180/year)
- ✅ **High ROI**: 2,700% over 3 years
- ✅ **Scalable**: Handles 2-3x growth with no cost increase
- ✅ **Simple**: Single license covers all three flows
- ✅ **Reliable**: Built on Microsoft's enterprise platform
- ✅ **Maintainable**: Low ongoing maintenance cost

**Recommendation**: Proceed with implementation using single per-user license.
