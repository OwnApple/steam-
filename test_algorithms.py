from utils import get_itemcf_recommendations, get_dssm_recommendations, load_ratings_data

def test_algorithms():
    print("Testing Load Data...")
    df = load_ratings_data()
    if df.empty:
        print("Error: Ratings table is empty or connection failed.")
        return
        
    print(f"Data loaded successfully! Total records: {len(df)}")
    
    # 找出一个存在的 user_id
    sample_user_id = df['user_id'].iloc[0]
    print(f"\n--- Testing with user_id: {sample_user_id} ---")
    
    print("\n1. Testing ItemCF Recommendations...")
    try:
        itemcf_recs = get_itemcf_recommendations(sample_user_id, top_n=5)
        print(f"ItemCF Recommendations (Top 5 Game IDs): {itemcf_recs}")
    except Exception as e:
        print(f"ItemCF Error: {e}")
        
    print("\n2. Testing DSSM Recommendations...")
    try:
        dssm_recs = get_dssm_recommendations(sample_user_id, top_n=5)
        print(f"DSSM Recommendations (Top 5 Game IDs): {dssm_recs}")
    except Exception as e:
        print(f"DSSM Error: {e}")

if __name__ == "__main__":
    test_algorithms()
