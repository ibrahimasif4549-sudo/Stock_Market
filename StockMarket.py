import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt


def test_shock_days_dividend_safe(ticker, start_date, end_date, drop_threshold_pct=5.0):
    yf_ticker = f"{ticker}.KA" if not ticker.endswith('.KA') else ticker

    print(f"Downloading dividend-adjusted data for {yf_ticker}...\n")

    stock = yf.Ticker(yf_ticker)
    df = stock.history(start=start_date, end=end_date, auto_adjust=True)

    if df.empty:
        print(f"No data found for {yf_ticker}.")
        return

    df = df.reset_index()
    price_col = 'Close'

    # 1. Calculate returns & identify shock days
    threshold = drop_threshold_pct / 100.0
    df['Daily_Return'] = df[price_col].pct_change()
    df['Is_Shock'] = df['Daily_Return'] <= -threshold

    # 2. Track 5, 10, 20 day returns
    horizons = [5, 10, 20]
    for h in horizons:
        df[f'Return_{h}d'] = df[price_col].shift(-h) / df[price_col] - 1

    # 3. Calculate 20-day path trajectory columns FIRST
    for i in range(21):
        df[f'Path_{i}'] = df[price_col].shift(-i) / df[price_col]

    # 4. Slice into shock and ordinary days (with path columns included)
    shock_days = df[df['Is_Shock']]
    ordinary_days = df[~df['Is_Shock'] & df['Daily_Return'].notna()]

    # 5. Summarize
    results = []
    for h in horizons:
        col = f'Return_{h}d'

        s_ret = shock_days[col].mean() * 100
        s_win = (shock_days[col] > 0).sum() / shock_days[col].notna().sum() * 100 if len(shock_days) > 0 else 0

        o_ret = ordinary_days[col].mean() * 100
        o_win = (ordinary_days[col] > 0).sum() / ordinary_days[col].notna().sum() * 100 if len(ordinary_days) > 0 else 0

        results.append({
            'Horizon': f'{h} Days',
            'Shock Avg Return (%)': round(s_ret, 2),
            'Shock Win Rate (%)': round(s_win, 2),
            'Baseline Avg Return (%)': round(o_ret, 2),
            'Baseline Win Rate (%)': round(o_win, 2)
        })

    summary_df = pd.DataFrame(results)
    print(f"--- {ticker} SUMMARY FOR ≥{drop_threshold_pct}% DROP ---")
    print(f"Total trading days analyzed: {len(df)}")
    print(f"Total pure shock days found (excluding dividend drops): {len(shock_days)}")
    print("-" * 65)
    print(summary_df.to_string(index=False))

    # 6. Chart
    if len(shock_days) > 0:
        path_cols = [f'Path_{i}' for i in range(21)]
        shock_paths = shock_days[path_cols].mean() * 100

        plt.figure(figsize=(10, 6))
        plt.plot(range(21), shock_paths, marker='o', linestyle='-', color='#1f77b4')
        plt.axhline(100, color='red', linestyle='--', label='Shock Day Close (Break-even)')
        plt.title(f'{ticker}: Avg 20-Day Recovery Following a ≥{drop_threshold_pct}% Drop')
        plt.xlabel('Trading Days After Shock')
        plt.ylabel('Indexed Price (Shock Close = 100)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()
    else:
        print(f"\nNo drops of {drop_threshold_pct}% or more found for {ticker} in this period.")

    return summary_df


# Run test enter stock name and period to be analyzed
test_shock_days_dividend_safe("ssgc", "2018-02-01", "2026-09-13", 5.0)

