//+------------------------------------------------------------------+
//|                                              SimpleMA_Test.mq4  |
//|                       Simple Moving Average for Testing         |
//+------------------------------------------------------------------+
#property copyright "Conversion Test"
#property version   "1.00"
#property strict
#property indicator_chart_window
#property indicator_buffers 2
#property indicator_color1 Blue
#property indicator_color2 Red

// Input parameters
input int    MA_Period_Fast = 10;    // Fast MA Period
input int    MA_Period_Slow = 20;    // Slow MA Period
input int    MA_Method = 0;          // MA Method (0=SMA, 1=EMA, 2=SMMA, 3=LWMA)
input int    Applied_Price = 0;      // Applied Price (0=Close, 1=Open, 2=High, 3=Low)

// Indicator buffers
double FastMABuffer[];
double SlowMABuffer[];

//+------------------------------------------------------------------+
//| Custom indicator initialization function                        |
//+------------------------------------------------------------------+
int OnInit()
{
   // Set indicator buffers
   SetIndexBuffer(0, FastMABuffer);
   SetIndexBuffer(1, SlowMABuffer);
   
   // Set indicator labels
   SetIndexLabel(0, "Fast MA(" + IntegerToString(MA_Period_Fast) + ")");
   SetIndexLabel(1, "Slow MA(" + IntegerToString(MA_Period_Slow) + ")");
   
   // Set indicator style
   SetIndexStyle(0, DRAW_LINE);
   SetIndexStyle(1, DRAW_LINE);
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                             |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
{
   int i, limit;
   
   // Calculate starting point
   if(prev_calculated == 0)
      limit = rates_total - MathMax(MA_Period_Fast, MA_Period_Slow);
   else
      limit = rates_total - prev_calculated;
   
   // Calculate Fast MA
   for(i = 0; i < limit; i++)
   {
      FastMABuffer[i] = iMA(NULL, 0, MA_Period_Fast, 0, MA_Method, Applied_Price, i);
   }
   
   // Calculate Slow MA
   for(i = 0; i < limit; i++)
   {
      SlowMABuffer[i] = iMA(NULL, 0, MA_Period_Slow, 0, MA_Method, Applied_Price, i);
   }
   
   return(rates_total);
}

//+------------------------------------------------------------------+
//| Export function for testing - calculates crossover signals      |
//+------------------------------------------------------------------+
int GetCrossoverSignal(int shift)
{
   // Returns: 1 for bullish crossover, -1 for bearish crossover, 0 for no signal
   
   if(shift < 1) return(0);
   
   double fast_current = FastMABuffer[shift];
   double fast_previous = FastMABuffer[shift + 1];
   double slow_current = SlowMABuffer[shift];
   double slow_previous = SlowMABuffer[shift + 1];
   
   // Bullish crossover (fast crosses above slow)
   if(fast_previous <= slow_previous && fast_current > slow_current)
      return(1);
   
   // Bearish crossover (fast crosses below slow)
   if(fast_previous >= slow_previous && fast_current < slow_current)
      return(-1);
   
   return(0);
}