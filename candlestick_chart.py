#!/usr/bin/env python3
"""
Candlestick Chart Generator for Market Data
Reads OHLC data from market_data.db and displays candlestick charts for tickers.
"""

import sqlite3
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
import argparse
import sys
from pathlib import Path


class CandlestickChartGenerator:
    """Generate candlestick charts from market data database."""
    
    def __init__(self, db_path: str = "market_data.db"):
        """Initialize with database path."""
        self.db_path = db_path
        if not Path(db_path).exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        
    def get_available_tickers(self) -> list:
        """Get all unique tickers from the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT ticker FROM ohlc_data ORDER BY ticker")
            tickers = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tickers
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
    
    def get_data_for_ticker(self, ticker: str) -> pd.DataFrame:
        """Get OHLC data for a specific ticker."""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT date, open, high, low, close, adj_close, volume 
                FROM ohlc_data 
                WHERE ticker = ? 
                ORDER BY date
            """
            df = pd.read_sql_query(query, conn, params=(ticker,))
            conn.close()
            
            if df.empty:
                print(f"No data found for ticker: {ticker}")
                return None
            
            # Convert date to datetime
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Ensure numeric types
            df['open'] = pd.to_numeric(df['open'], errors='coerce')
            df['high'] = pd.to_numeric(df['high'], errors='coerce')
            df['low'] = pd.to_numeric(df['low'], errors='coerce')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
            
            return df
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    
    def plot_candlestick(self, ticker: str, save_path: str = None):
        """Plot candlestick chart for a ticker."""
        df = self.get_data_for_ticker(ticker)
        
        if df is None or df.empty:
            return False
        
        try:
            # Define colors for candlesticks
            mc = mpf.make_marketcolors(up='g', down='r', volume='in')
            s = mpf.make_mpf_style(marketcolors=mc)
            
            # Create the plot
            title = f"{ticker} - Daily Candlestick Chart"
            
            if save_path:
                mpf.plot(df, type='candle', title=title, style=s, volume=True,
                        savefig=dict(fname=save_path, dpi=100))
                print(f"Chart saved to: {save_path}")
            else:
                mpf.plot(df, type='candle', title=title, style=s, volume=True)
            
            return True
        except Exception as e:
            print(f"Error plotting chart for {ticker}: {e}")
            return False
    
    def plot_multiple_tickers(self, tickers: list, save_dir: str = None):
        """Plot candlestick charts for multiple tickers."""
        if save_dir:
            Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        success_count = 0
        for ticker in tickers:
            print(f"\nGenerating chart for {ticker}...")
            save_path = None
            if save_dir:
                save_path = f"{save_dir}/{ticker}_candlestick.png"
            
            if self.plot_candlestick(ticker, save_path):
                success_count += 1
        
        return success_count
    
    def plot_multiple_subplots(self, tickers: list, save_path: str = None):
        """Plot multiple tickers in subplots (matplotlib style)."""
        valid_tickers = []
        dfs = {}
        
        for ticker in tickers:
            df = self.get_data_for_ticker(ticker)
            if df is not None and not df.empty:
                valid_tickers.append(ticker)
                dfs[ticker] = df
        
        if not valid_tickers:
            print("No valid data found for any tickers")
            return False
        
        try:
            # Create subplots
            num_tickers = len(valid_tickers)
            num_cols = min(2, num_tickers)
            num_rows = (num_tickers + num_cols - 1) // num_cols
            
            fig, axes = plt.subplots(num_rows, num_cols, figsize=(15, 5*num_rows))
            
            # Flatten axes array if needed
            if num_rows == 1 and num_cols == 1:
                axes = [axes]
            elif num_rows == 1 or num_cols == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()
            
            for idx, ticker in enumerate(valid_tickers):
                ax = axes[idx]
                df = dfs[ticker]
                
                # Plot candlesticks
                width = 0.6
                
                # Green candles (up)
                up = df[df['close'] >= df['open']]
                ax.bar(up.index, up['close'] - up['open'], width, 
                       bottom=up['open'], color='g', label='Up')
                ax.plot(up.index, up['high'], 'g-', linewidth=0.5)
                ax.plot(up.index, up['low'], 'g-', linewidth=0.5)
                
                # Red candles (down)
                down = df[df['close'] < df['open']]
                ax.bar(down.index, down['close'] - down['open'], width,
                       bottom=down['close'], color='r', label='Down')
                ax.plot(down.index, down['high'], 'r-', linewidth=0.5)
                ax.plot(down.index, down['low'], 'r-', linewidth=0.5)
                
                ax.set_title(f"{ticker} - Daily Candlestick Chart")
                ax.set_xlabel("Date")
                ax.set_ylabel("Price (USD)")
                ax.grid(True, alpha=0.3)
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
            
            # Hide unused subplots
            for idx in range(len(valid_tickers), len(axes)):
                axes[idx].set_visible(False)
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=100, bbox_inches='tight')
                print(f"\nChart saved to: {save_path}")
            else:
                plt.show()
            
            return True
        except Exception as e:
            print(f"Error creating subplots: {e}")
            return False


def main():
    """Main function to handle command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate candlestick charts from market data"
    )
    parser.add_argument(
        "--db", 
        default="market_data.db",
        help="Path to market_data.db (default: market_data.db)"
    )
    parser.add_argument(
        "--ticker",
        help="Specific ticker to plot (e.g., BTC-USD)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Plot all tickers"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available tickers"
    )
    parser.add_argument(
        "--save-dir",
        help="Directory to save charts (individual files)"
    )
    parser.add_argument(
        "--save-file",
        help="File to save combined chart"
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Plot multiple tickers in subplots"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    try:
        generator = CandlestickChartGenerator(args.db)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Handle different commands
    if args.list:
        tickers = generator.get_available_tickers()
        if tickers:
            print(f"Available tickers ({len(tickers)}):")
            for ticker in tickers:
                print(f"  - {ticker}")
        else:
            print("No tickers found in database")
        return
    
    if args.all:
        tickers = generator.get_available_tickers()
        if not tickers:
            print("No tickers found in database")
            return
        print(f"Generating charts for {len(tickers)} tickers...")
        if args.combined:
            generator.plot_multiple_subplots(tickers, args.save_file)
        else:
            count = generator.plot_multiple_tickers(tickers, args.save_dir)
            print(f"\nSuccessfully generated {count}/{len(tickers)} charts")
        return
    
    if args.ticker:
        generator.plot_candlestick(args.ticker, args.save_file)
        return
    
    # Default: show all tickers and ask for input
    tickers = generator.get_available_tickers()
    if not tickers:
        print("No tickers found in database")
        return
    
    print("Available tickers:")
    for i, ticker in enumerate(tickers, 1):
        print(f"  {i}. {ticker}")
    
    print("\nUsage Examples:")
    print(f"  python candlestick_chart.py --list                    # List all tickers")
    print(f"  python candlestick_chart.py --ticker BTC-USD          # Plot BTC-USD")
    print(f"  python candlestick_chart.py --all --save-dir charts   # Save all charts")
    print(f"  python candlestick_chart.py --all --combined           # Show all in subplots")
    print(f"  python candlestick_chart.py --all --combined --save-file all_tickers.png")


if __name__ == "__main__":
    main()
