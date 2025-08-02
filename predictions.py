def compute_simple_insights(df, window=100):
    recent = df.sort_values(["Date"], ascending=False).head(window)
    insights = {"common": {}, "uncommon": {}}
    for pos in ["Digit1", "Digit2", "Digit3"]:
        counts = recent[pos].value_counts()
        if not counts.empty:
            insights["common"][pos] = int(counts.idxmax())
            insights["uncommon"][pos] = int(counts.idxmin())
        else:
            insights["common"][pos] = None
            insights["uncommon"][pos] = None
    return insights
