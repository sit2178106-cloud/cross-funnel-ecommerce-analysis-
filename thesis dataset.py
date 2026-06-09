import pandas as pd
import numpy as np
import random

np.random.seed(42)
random.seed(42)

print("Prada 2025 E-Commerce Simulation Initialized... (Applying 20% Variance & Multi-Year CLV)")


# PARAMETERS

N_TOP = 25000  
N_MID = 5000000 
N_CUST = 350000

regions = ['Japan', 'Rest of APAC', 'Europe', 'North America']

regional_cost_multiplier = {
    'Japan': 1.40,
    'Rest of APAC': 1.40,   
    'Europe': 1.18,           
    'North America': 1.0  
}

# TOP FUNNEL BASE


print("Generating Top Funnel Base...")

platforms = ['Google Ads', 'Bing Ads', 'Instagram', 'TikTok', 'YouTube', 'X', 'Email', 'SMS']

def get_campaign_category(platform):
    if platform in ['Google Ads', 'Bing Ads']: return 'Paid Search'
    elif platform in ['Instagram', 'TikTok', 'YouTube', 'X']: return 'Paid Social Media'
    elif platform == 'Email': return 'Email'
    elif platform == 'SMS': return 'SMS'

def get_campaign_type(category, platform):
    if category == 'Paid Search':
        return np.random.choice(['Brand Keywords (Prada, Miu Miu)', 'Generic Luxury Keywords (Designer bag, luxury shoes)', 'Competitor Conquesting'], p=[0.60, 0.30, 0.10])
    elif category == 'Paid Social Media':
        if platform == 'TikTok': return np.random.choice(['Influencer/KOL (Viral/Trend)', 'Product Highlight (Short-form)', 'Brand Awareness (Behind the scenes)'], p=[0.50, 0.30, 0.20])
        elif platform == 'YouTube': return np.random.choice(['Brand Awareness (Cinematic/Editorial)', 'Influencer/KOL (Long-form/Vlog)', 'Product Highlight (Detailed Review)'], p=[0.50, 0.30, 0.20])
        elif platform == 'X': return np.random.choice(['Brand Awareness (Conversation Driven)', 'Product Launch Announcement', 'Influencer/KOL Discussion'], p=[0.40, 0.40, 0.20])
        else: return np.random.choice(['Brand Awareness (Editorial/Runway)', 'Influencer/KOL (Celebrity)', 'Product Highlight (Carousel)', 'Promo/Giveaway (Limited Drop)'], p=[0.30, 0.35, 0.25, 0.10])
    elif category == 'Email': return np.random.choice(['Welcome Series', 'Cart Abandonment Flow', 'VIP Early Access / Private Sale', 'Newsletter / Brand Story'], p=[0.20, 0.35, 0.25, 0.20])
    elif category == 'SMS': return np.random.choice(['Flash Sale / Price Drop Alert', 'Cart Abandonment Alert', 'Back-in-Stock Alert', 'VIP Event Invitation'], p=[0.30, 0.40, 0.20, 0.10])

top_rows_base = []
for i in range(N_TOP):
    region = np.random.choice(regions, p=[0.13, 0.33, 0.31, 0.23])
    platform = np.random.choice(platforms, p=[0.25, 0.05, 0.20, 0.10, 0.10, 0.05, 0.125, 0.125])
    category = get_campaign_category(platform)
    campaign_type = get_campaign_type(category, platform)

    if category == 'Paid Search':
        target_ctr = np.random.uniform(0.04, 0.10)
        target_er = 0
        target_cpc = np.random.uniform(2.5, 6.0)
    elif category == 'Paid Social Media':
        target_ctr = np.random.uniform(0.015, 0.035)
        target_er = np.random.uniform(0.03, 0.08)
        target_cpc = np.random.uniform(0.5, 1.5)
        if platform == 'TikTok': target_er *= 1.5
    elif category == 'Email':
        target_ctr = np.random.uniform(0.03, 0.08)
        target_er = 0
        target_cpc = 0.005
    else:
        target_ctr = np.random.uniform(0.05, 0.12)
        target_er = 0
        target_cpc = 0.01

    top_rows_base.append({
        'Campaign_ID': f'CMP_{i:05d}',
        'Region': region,
        'Platform': platform,
        'Campaign_Category': category,
        'Campaign_Type': campaign_type,
        'Target_CTR': target_ctr,
        'Target_ER': target_er,
        'Target_CPC': target_cpc
    })

df_top_base = pd.DataFrame(top_rows_base)
camp_info = df_top_base.set_index('Campaign_ID').to_dict('index')


# MID FUNNEL 

print("Generating Mid Funnel (5 Million Sessions)...")

customer_ids = [f'CUST_{i:06d}' for i in range(N_CUST)]
customer_types = np.random.choice(['New', 'Returning'], N_CUST, p=[0.40, 0.60])
cust_type_dict = dict(zip(customer_ids, customer_types))

new_cust_ids_arr = [k for k, v in cust_type_dict.items() if v == 'New']
ret_cust_ids_arr = [k for k, v in cust_type_dict.items() if v == 'Returning']
len_new = len(new_cust_ids_arr)
len_ret = len(ret_cust_ids_arr)

traffic_sources = ['Organic Search', 'Direct', 'Paid Search', 'Paid Social Media', 'Email', 'SMS']

campaign_dict = {
    'Paid Search': df_top_base[df_top_base['Campaign_Category'] == 'Paid Search']['Campaign_ID'].tolist(),
    'Paid Social Media': df_top_base[df_top_base['Campaign_Category'] == 'Paid Social Media']['Campaign_ID'].tolist(),
    'Email': df_top_base[df_top_base['Campaign_Category'] == 'Email']['Campaign_ID'].tolist(),
    'SMS': df_top_base[df_top_base['Campaign_Category'] == 'SMS']['Campaign_ID'].tolist()
}

cr_targets = {'Paid Social Media': 0.0450, 'Direct': 0.0192, 'Organic Search': 0.0169, 'Paid Search': 0.0050, 'Email': 0.0261, 'SMS': 0.0326}
source_aov_mult = {'Direct': 1.05, 'Organic Search': 0.98, 'Paid Search': 0.95, 'Paid Social Media': 0.92, 'Email': 1.02, 'SMS': 1.05}

def get_base_aov(region):
    if region == 'Japan': return 820
    elif region == 'Rest of APAC': return 610
    elif region == 'Europe': return 505
    else: return 515

regions_arr = np.random.choice(regions, size=N_MID, p=[0.13, 0.33, 0.31, 0.23])
sources_arr = np.random.choice(traffic_sources, size=N_MID, p=[0.45, 0.35, 0.12, 0.02, 0.03, 0.03])
rands = np.random.rand(N_MID, 7)

mid_rows = []

for i in range(N_MID):
    region = regions_arr[i]
    source = sources_arr[i]
    
    req_type = None 
    campaign_id = np.nan
    camp_type = None
    platform = None
    
    if source in campaign_dict and len(campaign_dict[source]) > 0:
        campaign_id = random.choice(campaign_dict[source])
        camp_type = camp_info[campaign_id]['Campaign_Type']
        platform = camp_info[campaign_id]['Platform']

    force_no_trans = False

    if camp_type:
        if camp_type in ["Brand Awareness (Editorial/Runway)", "Brand Awareness (Behind the scenes)", "Brand Awareness (Conversation Driven)", "Influencer/KOL Discussion", "Brand Awareness (Cinematic/Editorial)"]: force_no_trans = True
        elif platform == 'Bing Ads' and camp_type == 'Competitor Conquesting': force_no_trans = True
        elif camp_type in ["VIP Early Access / Private Sale", "VIP Event Invitation", "Back-in-Stock Alert", "Flash Sale / Price Drop Alert", "Newsletter / Brand Story"]: req_type = 'Returning'
        elif camp_type in ["Welcome Series", "Influencer/KOL (Viral/Trend)"]: req_type = 'New'
        elif platform == 'Google Ads' and camp_type == 'Competitor Conquesting': req_type = 'New'
        elif platform == 'Bing Ads' and camp_type == 'Generic Luxury Keywords (Designer bag, luxury shoes)': req_type = 'New'
        elif camp_type == 'Brand Keywords (Prada, Miu Miu)': req_type = 'Returning' if rands[i, 1] < 0.80 else 'New'
        elif platform == 'Google Ads' and camp_type == 'Generic Luxury Keywords (Designer bag, luxury shoes)': req_type = 'New' if rands[i, 1] < 0.80 else 'Returning'
        elif camp_type in ['Influencer/KOL (Celebrity)', 'Product Highlight (Short-form)', 'Influencer/KOL (Long-form/Vlog)']: req_type = 'New' if rands[i, 1] < 0.80 else 'Returning'
        elif camp_type == 'Promo/Giveaway (Limited Drop)': req_type = 'Returning' if rands[i, 1] < 0.80 else 'New'
        elif camp_type == 'Product Highlight (Detailed Review)': req_type = 'New' if rands[i, 1] < 0.50 else 'Returning'

    if req_type is None:
        if source == 'Direct': req_type = 'Returning' if rands[i, 0] < 0.70 else 'New'
        elif source == 'Organic Search': req_type = 'New' if rands[i, 0] < 0.60 else 'Returning'
        else: req_type = 'New' if rands[i, 0] < 0.50 else 'Returning'

    cust_id = new_cust_ids_arr[int(rands[i, 2] * len_new)] if req_type == 'New' else ret_cust_ids_arr[int(rands[i, 2] * len_ret)]

    bounce_prob = 0.42
    if source in ['Direct', 'Organic Search']: bounce_prob = 0.35
    elif source == 'Paid Social Media': bounce_prob = 0.55
    bounce = (rands[i, 3] < bounce_prob)

    atc, transaction, revenue = 0, 0, 0

    if not bounce:
        cr = cr_targets[source]
        if region == 'Japan': cr *= 1.25
        elif region == 'Rest of APAC': cr *= 1.10
        elif region == 'Europe': cr *= 0.95
        else: cr *= 0.85

        if camp_type:
            if camp_type in ['Cart Abandonment Flow', 'Cart Abandonment Alert']: cr *= 2.0
            elif camp_type == 'Back-in-Stock Alert': cr *= 1.8
            elif camp_type == 'Brand Keywords (Prada, Miu Miu)': cr *= 2.5
            elif camp_type == 'Influencer/KOL (Viral/Trend)': cr *= 0.10 
            elif platform == 'Google Ads' and camp_type == 'Competitor Conquesting': cr *= 0.05

        if req_type == 'Returning': cr *= 1.20
        cr = min(cr, 0.08) 

        atc_prob = min(cr * 6, 0.85)
        if rands[i, 4] < atc_prob:
            atc = 1
            if not force_no_trans:
                purchase_prob = cr / atc_prob
                if rands[i, 5] < purchase_prob:
                    transaction = 1
                    base_aov = get_base_aov(region) * source_aov_mult[source]
                    revenue = max(base_aov * random.gauss(1.0, 0.15), base_aov * 0.5)

    if transaction == 0:
        anon_prob = 0.30 if (atc == 1 and req_type == 'New') else (0.05 if atc == 1 else (0.70 if req_type == 'New' else 0.20))
        if rands[i, 6] < anon_prob: cust_id = np.nan 

    mid_rows.append([f'SES_{i:08d}', cust_id, campaign_id, region, source, 1, int(bounce), atc, transaction, round(revenue, 2)])

df_mid = pd.DataFrame(mid_rows, columns=['Session_ID', 'Customer_ID', 'Campaign_ID', 'Region', 'Traffic_Source', 'Website_Sessions', 'Bounces', 'Add_To_Cart_Events', 'Transactions', 'Total_Revenue'])


# FUNNEL LINKAGE 

print("Syncing Ad Spend perfectly with Website Sessions to fix ROI...")

session_counts = df_mid[df_mid['Campaign_ID'].notna()].groupby('Campaign_ID').size().to_dict()

top_rows_final = []
for row in top_rows_base:
    camp_id = row['Campaign_ID']
    region = row['Region']
    
    actual_sessions = session_counts.get(camp_id, 0)
    if actual_sessions == 0:
        actual_sessions = random.randint(10, 50)
        
    clicks = int(actual_sessions * random.uniform(1.02, 1.10))
    impressions = int(clicks / row['Target_CTR'])
    engagements = int(impressions * row['Target_ER'])
    
    cpc = row['Target_CPC'] * regional_cost_multiplier[region]
    spend = round(clicks * cpc, 2)
    
    top_rows_final.append({
        'Campaign_ID': camp_id,
        'Region': region,
        'Platform': row['Platform'],
        'Campaign_Category': row['Campaign_Category'],
        'Campaign_Type': row['Campaign_Type'],
        'Impressions': impressions,
        'Clicks': clicks,
        'Total_Engagements': engagements,
        'Campaign_Ad_Spend': spend
    })

df_top = pd.DataFrame(top_rows_final)

# Extracting only APAC data
df_top['Region'] = df_top['Region'].replace({'Japan': 'APAC', 'Rest of APAC': 'APAC'})
df_mid['Region'] = df_mid['Region'].replace({'Japan': 'APAC', 'Rest of APAC': 'APAC'})



# BOTTOM FUNNEL 

print("Generating Bottom Funnel (Applying 20% Noise for ANOVA & Multi-Year CLV)...")

identified = df_mid[(df_mid['Bounces'] == 0) & (df_mid['Customer_ID'].notna())].copy()
history_agg = identified.groupby('Customer_ID').agg({'Region': 'first', 'Total_Revenue': 'sum', 'Transactions': 'sum'}).reset_index()

bottom_rows = []
for _, row in history_agg.iterrows():
    cust_id = row['Customer_ID']
    region = row['Region']
    revenue = row['Total_Revenue']
    tx_count = row['Transactions']
    customer_type = cust_type_dict[cust_id]

    if customer_type == 'Returning':
        past_freq = random.randint(3, 10)
        # MULTI-YEAR CLV: 5 years of CLV history simulation
        past_ltv = max(random.gauss(4500, 1000), 1500) 
    else:
        past_freq = 0
        past_ltv = 0

    total_freq = tx_count + past_freq
    total_ltv = revenue + past_ltv

    if customer_type == 'New':
        if region == 'APAC':
            base_cac = 895
        elif region == 'Europe':
            base_cac = 835
        else: # North America
            base_cac = 795
        
        spend = base_cac * np.random.normal(1.0, 0.20)
    else:
        spend = random.gauss(15, 5) 

    spend = max(spend, 10.0) 

    bottom_rows.append({
        'Customer_ID': cust_id,
        'Region': region,
        'Customer_Type': customer_type,
        'New_Customers_Acquired': 1 if (customer_type == 'New' and tx_count > 0) else 0,
        'Returning_Customers': 1 if (customer_type == 'Returning' and tx_count > 0) else 0,
        'Total_Marketing_Spend': round(spend, 2),
        'Historical_Purchase_Frequency': total_freq,
        'Historical_Ecom_Lifetime_Value': total_ltv, 
        'Historical_AOV': 0
    })

df_bot = pd.DataFrame(bottom_rows)

df_bot['Historical_Ecom_Lifetime_Value'] = df_bot['Historical_Ecom_Lifetime_Value'].round(2)
df_bot['Historical_AOV'] = np.where(
    df_bot['Historical_Purchase_Frequency'] > 0,
    round(df_bot['Historical_Ecom_Lifetime_Value'] / df_bot['Historical_Purchase_Frequency'], 2),
    0
)


# EXPORT

df_top.to_csv('top_funnel_prada_2025.csv', index=False)
df_mid.to_csv('mid_funnel_prada_2025.csv', index=False)
df_bot.to_csv('bottom_funnel_prada_2025.csv', index=False)

print("\nSUCCESS")
print("Prada 2025 datasets exported with EXACT ANOVA noise and MULTI-YEAR CLV horizons.")