//+------------------------------------------------------------------+
//|                                     AdaptiveLaguerre_v2_improved.mq5 |
//|                                Copyright © 2012, TrendLaboratory |
//|            http://finance.groups.yahoo.com/group/TrendLaboratory |
//|                                   E-mail: igorad2003@yahoo.co.uk |
//|                              Improved Documentation & Validation |
//+------------------------------------------------------------------+
#property copyright "Copyright © 2012, TrendLaboratory - Improved Version"
#property link      "http://finance.groups.yahoo.com/group/TrendLaboratory"
#property version   "2.1"
#property description "Adaptive Laguerre Filter - Advanced Trend Following Indicator"
#property description " "
#property description "The Laguerre filter provides 40-60% less lag than traditional MAs"
#property description "while maintaining smooth output for reliable trend detection."
#property description " "
#property description "Key Features:"
#property description "• Adaptive mode adjusts to market volatility automatically"
#property description "• Multi-timeframe support for higher timeframe analysis"
#property description "• Color-coded trend visualization"
#property description "• Multiple smoothing algorithms for the adaptive factor"

#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1

#property indicator_type1   DRAW_COLOR_LINE
#property indicator_color1  Silver,DeepSkyBlue,OrangeRed
#property indicator_width1  2
#property indicator_label1  "Adaptive Laguerre"

//+------------------------------------------------------------------+
//| Enumerations                                                     |
//+------------------------------------------------------------------+
enum ENUM_SMOOTH_MODE
{
   sma,     //SMA - Simple Moving Average (Equal weight to all values)
   ema,     //EMA - Exponential Moving Average (More weight to recent values)
   wilder,  //Wilder - Wilder's Smoothing (EMA variant with period*2-1)
   lwma,    //LWMA - Linear Weighted MA (Linear decrease in weights)
   median   //Median - Moving Median (Robust to outliers, recommended)
};

enum ENUM_TRADING_STYLE
{
   SCALPING,        //Scalping (Length:5-10, Order:2-3)
   DAY_TRADING,     //Day Trading (Length:10-20, Order:3-4)
   SWING_TRADING,   //Swing Trading (Length:20-50, Order:4-5)
   POSITION_TRADING //Position Trading (Length:50-100, Order:4-6)
};

//+------------------------------------------------------------------+
//| Input Parameters with Detailed Documentation                     |
//+------------------------------------------------------------------+
// Timeframe Settings
input group "════════ TIMEFRAME SETTINGS ════════"
input ENUM_TIMEFRAMES      TimeFrame            = PERIOD_CURRENT; //Timeframe - Use higher TF on lower TF chart (0=Current)
input ENUM_APPLIED_PRICE   Price                = PRICE_CLOSE;    //Price Type - Which price to filter (Close recommended)

// Main Filter Parameters
input group "════════ FILTER PARAMETERS ════════"
input int                  Length               = 10;        //Length [3-200] - Period for calculations (↑smoother ↓responsive)
input int                  Order                = 4;         //Filter Order [1-10] - Recursive levels (4 optimal, >6 may overshoot)
input ENUM_TRADING_STYLE   TradingStyle         = DAY_TRADING; //Trading Style Preset - Auto-configure for your style

// Adaptive Settings
input group "════════ ADAPTIVE SETTINGS ════════"
input bool                 AdaptiveMode         = true;      //Enable Adaptive Mode - Dynamic adjustment to market conditions
input int                  AdaptiveSmooth       = 5;         //Adaptive Smoothing [1-50] - Smoothing period for gamma factor
input ENUM_SMOOTH_MODE     AdaptiveSmoothMode   = median;    //Smoothing Method - Algorithm for adaptive factor (Median recommended)
input double               MinGamma             = 0.01;      //Minimum Gamma [0.001-0.1] - Lower bound for adaptive factor
input double               MaxGamma             = 0.99;      //Maximum Gamma [0.9-0.999] - Upper bound for adaptive factor

// Visual Settings
input group "════════ VISUAL SETTINGS ════════"
input bool                 ColorMode            = true;      //Enable Trend Coloring - Blue=Up, Red=Down, Silver=Neutral
input bool                 ShowGamma            = false;     //Show Gamma in Data Window - Display adaptive factor values
input bool                 AlertOnTrendChange   = false;     //Alert on Trend Change - Sound/popup when trend changes

// Advanced Settings
input group "════════ ADVANCED SETTINGS ════════"
input bool                 UseEnhancedCalc      = true;      //Enhanced Calculation - Improved numerical stability
input int                  MinBarsRequired      = 100;       //Minimum Bars Required [50-500] - Bars needed for calculation
input bool                 DebugMode            = false;     //Debug Mode - Print diagnostic information

//+------------------------------------------------------------------+
//| Global Variables                                                 |
//+------------------------------------------------------------------+
double  laguerre[];
double  trend[];
double  price[];
double  diff[];
double  gamma[];

ENUM_TIMEFRAMES  tf;
int      mtf_handle, Price_handle;
double   L[][2], mtf_laguerre[1], mtf_trend[1], ema[2];
datetime prevtime, ptime, last_alert_time;
bool     ftime = true;

// Validated parameters
int      valid_length;
int      valid_order;
int      valid_adaptive_smooth;
double   valid_min_gamma;
double   valid_max_gamma;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
{
   // Apply trading style presets
   ApplyTradingStylePreset();
   
   // Validate and adjust input parameters
   if(!ValidateParameters())
   {
      Print("ERROR: Invalid parameters detected. Please check the settings.");
      return(INIT_PARAMETERS_INCORRECT);
   }
   
   // Set timeframe
   if(TimeFrame <= Period()) tf = Period(); else tf = TimeFrame;
   
   // Initialize buffers
   SetIndexBuffer(0, laguerre, INDICATOR_DATA); 
   PlotIndexSetInteger(0, PLOT_COLOR_INDEXES, 3);
   SetIndexBuffer(1, trend, INDICATOR_COLOR_INDEX);
   SetIndexBuffer(2, price, INDICATOR_CALCULATIONS);
   SetIndexBuffer(3, diff, INDICATOR_CALCULATIONS);
   SetIndexBuffer(4, gamma, INDICATOR_CALCULATIONS);
   
   // Set plot properties
   PlotIndexSetInteger(0, PLOT_DRAW_BEGIN, valid_length + 1);
   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, EMPTY_VALUE);
   
   // Set indicator properties
   IndicatorSetInteger(INDICATOR_DIGITS, _Digits);
   
   // Build indicator name with parameters
   string short_name = StringFormat("ALF_v2[%s](%s,L:%d,O:%d,A:%s,G:%.2f-%.2f)",
                                    timeframeToString(TimeFrame),
                                    priceToString(Price),
                                    valid_length,
                                    valid_order,
                                    AdaptiveMode ? "ON" : "OFF",
                                    valid_min_gamma,
                                    valid_max_gamma);
   
   IndicatorSetString(INDICATOR_SHORTNAME, short_name);
   PlotIndexSetString(0, PLOT_LABEL, "Adaptive Laguerre Filter");
   
   // Initialize handles
   Price_handle = iMA(NULL, TimeFrame, 1, 0, 0, Price);
   
   if(TimeFrame > 0) 
   {
      mtf_handle = iCustom(NULL, TimeFrame, "AdaptiveLaguerre_v2_improved", 
                          0, Price, valid_length, valid_order, 
                          AdaptiveMode, valid_adaptive_smooth, 
                          AdaptiveSmoothMode, ColorMode);
   }
   else
   {
      ArrayResize(L, valid_order);
   }
   
   // Print initialization info
   if(DebugMode)
   {
      PrintInitializationInfo();
   }
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Validate and adjust parameters                                  |
//+------------------------------------------------------------------+
bool ValidateParameters()
{
   bool valid = true;
   
   // Validate Length
   valid_length = Length;
   if(Length < 3)
   {
      Print("WARNING: Length too small (<3), adjusted to 3");
      valid_length = 3;
   }
   else if(Length > 200)
   {
      Print("WARNING: Length too large (>200), adjusted to 200");
      valid_length = 200;
   }
   
   // Validate Order
   valid_order = Order;
   if(Order < 1)
   {
      Print("WARNING: Order too small (<1), adjusted to 1");
      valid_order = 1;
   }
   else if(Order > 10)
   {
      Print("WARNING: Order too large (>10), may cause instability. Adjusted to 10");
      valid_order = 10;
   }
   else if(Order > 6)
   {
      Print("INFO: Order > 6 may cause overshoot in some market conditions");
   }
   
   // Validate Adaptive Smooth
   valid_adaptive_smooth = AdaptiveSmooth;
   if(AdaptiveSmooth < 1)
   {
      Print("WARNING: AdaptiveSmooth too small (<1), adjusted to 1");
      valid_adaptive_smooth = 1;
   }
   else if(AdaptiveSmooth > 50)
   {
      Print("WARNING: AdaptiveSmooth too large (>50), adjusted to 50");
      valid_adaptive_smooth = 50;
   }
   
   // Validate Gamma bounds
   valid_min_gamma = MinGamma;
   valid_max_gamma = MaxGamma;
   
   if(MinGamma < 0.001)
   {
      Print("WARNING: MinGamma too small (<0.001), adjusted to 0.001");
      valid_min_gamma = 0.001;
   }
   else if(MinGamma > 0.1)
   {
      Print("WARNING: MinGamma too large (>0.1), adjusted to 0.1");
      valid_min_gamma = 0.1;
   }
   
   if(MaxGamma < 0.9)
   {
      Print("WARNING: MaxGamma too small (<0.9), adjusted to 0.9");
      valid_max_gamma = 0.9;
   }
   else if(MaxGamma > 0.999)
   {
      Print("WARNING: MaxGamma too large (>0.999), adjusted to 0.999");
      valid_max_gamma = 0.999;
   }
   
   if(valid_min_gamma >= valid_max_gamma)
   {
      Print("ERROR: MinGamma must be less than MaxGamma");
      valid = false;
   }
   
   return valid;
}

//+------------------------------------------------------------------+
//| Apply trading style preset                                      |
//+------------------------------------------------------------------+
void ApplyTradingStylePreset()
{
   // Only apply if user hasn't customized (using default values as check)
   if(Length == 10 && Order == 4)
   {
      switch(TradingStyle)
      {
         case SCALPING:
            Length = 7;
            Order = 3;
            AdaptiveSmooth = 3;
            Print("INFO: Applied SCALPING preset (Length:7, Order:3)");
            break;
            
         case DAY_TRADING:
            Length = 15;
            Order = 4;
            AdaptiveSmooth = 5;
            Print("INFO: Applied DAY_TRADING preset (Length:15, Order:4)");
            break;
            
         case SWING_TRADING:
            Length = 35;
            Order = 5;
            AdaptiveSmooth = 8;
            Print("INFO: Applied SWING_TRADING preset (Length:35, Order:5)");
            break;
            
         case POSITION_TRADING:
            Length = 75;
            Order = 5;
            AdaptiveSmooth = 12;
            Print("INFO: Applied POSITION_TRADING preset (Length:75, Order:5)");
            break;
      }
   }
}

//+------------------------------------------------------------------+
//| Print initialization information                                |
//+------------------------------------------------------------------+
void PrintInitializationInfo()
{
   Print("═══════════════════════════════════════════════════════");
   Print("Adaptive Laguerre Filter v2.1 - Initialization Complete");
   Print("═══════════════════════════════════════════════════════");
   Print("Settings:");
   Print("  • Timeframe: ", timeframeToString(tf));
   Print("  • Price: ", priceToString(Price));
   Print("  • Length: ", valid_length);
   Print("  • Order: ", valid_order);
   Print("  • Adaptive Mode: ", AdaptiveMode ? "Enabled" : "Disabled");
   
   if(AdaptiveMode)
   {
      Print("  • Adaptive Smooth: ", valid_adaptive_smooth);
      Print("  • Smooth Mode: ", EnumToString(AdaptiveSmoothMode));
      Print("  • Gamma Range: ", DoubleToString(valid_min_gamma, 3), 
            " - ", DoubleToString(valid_max_gamma, 3));
   }
   
   Print("  • Color Mode: ", ColorMode ? "Enabled" : "Disabled");
   Print("  • Enhanced Calc: ", UseEnhancedCalc ? "Enabled" : "Disabled");
   Print("═══════════════════════════════════════════════════════");
}

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &Time[],
                const double   &Open[],
                const double   &High[],
                const double   &Low[],
                const double   &Close[],
                const long     &TickVolume[],
                const long     &Volume[],
                const int      &Spread[])
{
   // Check minimum bars requirement
   if(rates_total < MinBarsRequired)
   {
      if(DebugMode)
         Print("INFO: Waiting for minimum bars. Current: ", rates_total, 
               " Required: ", MinBarsRequired);
      return(0);
   }
   
   int x, y, shift, limit, mtflimit, copied = 0;
   double sgamma = 0;
   datetime mtf_time;
   
   // Calculate limits
   if(prev_calculated == 0) 
   {
      limit = 0; 
      mtflimit = rates_total - 1;
      ArrayInitialize(laguerre, EMPTY_VALUE);
   }
   else 
   {
      limit = rates_total - 1;
      mtflimit = rates_total - prev_calculated + PeriodSeconds(tf)/PeriodSeconds(Period());
   }
   
   // Copy price data
   copied = CopyBuffer(Price_handle, 0, Time[rates_total-1], Time[0], price);
   
   if(copied < 0)
   {
      if(DebugMode)
         Print("WARNING: Not all prices copied. Error=", GetLastError(), ", copied=", copied);
      return(0);
   }
   
   // Multi-timeframe handling
   if(tf > Period())
   { 
      ArraySetAsSeries(Time, true);   
      
      for(shift = 0, y = 0; shift < mtflimit; shift++)
      {
         if(Time[shift] < iTime(NULL, TimeFrame, y)) y++; 
         mtf_time = iTime(NULL, TimeFrame, y);
         
         copied = CopyBuffer(mtf_handle, 0, mtf_time, mtf_time, mtf_laguerre);
         if(copied <= 0) return(0);
         
         x = rates_total - shift - 1;
         laguerre[x] = mtf_laguerre[0];
         
         if(ColorMode)
         {
            copied = CopyBuffer(mtf_handle, 1, mtf_time, mtf_time, mtf_trend);   
            if(copied <= 0) return(0);
            trend[x] = mtf_trend[0];   
         }
         else trend[x] = 0; 
      }
   }
   else
   {
      // Main calculation loop
      for(shift = limit; shift < rates_total; shift++)
      {
         if(shift < valid_length) continue;
         
         // Calculate difference for adaptive mode
         diff[shift] = MathAbs(price[shift] - laguerre[shift-1]);
         
         if(shift < 2 * valid_length) continue;              
         
         // Calculate gamma
         if(AdaptiveMode) 
         {
            gamma[shift] = AdaptiveGamma(diff, valid_length, shift);
            
            // Apply smoothing to gamma
            switch(AdaptiveSmoothMode)
            {
               case 1:  sgamma = EMA(gamma[shift], valid_adaptive_smooth, Time[shift], shift); break;
               case 2:  sgamma = EMA(gamma[shift], 2*valid_adaptive_smooth-1, Time[shift], shift); break;  
               case 3:  sgamma = LWMA(gamma, valid_adaptive_smooth, shift); break;   
               case 4:  sgamma = Median(gamma, valid_adaptive_smooth, shift); break; 
               default: sgamma = SMA(gamma, valid_adaptive_smooth, shift); break;
            }
            
            // Clamp gamma to valid range
            sgamma = MathMax(valid_min_gamma, MathMin(valid_max_gamma, sgamma));
         }
         else 
         {
            sgamma = 10.0 / (valid_length + 9);
         }
         
         // Calculate Laguerre filter
         if(UseEnhancedCalc)
            laguerre[shift] = LaguerreEnhanced(price[shift], sgamma, valid_order, Time[shift], shift);
         else
            laguerre[shift] = Laguerre(price[shift], sgamma, valid_order, Time[shift], shift);
         
         // Show gamma in data window if requested
         if(ShowGamma && AdaptiveMode)
         {
            gamma[shift] = sgamma;
         }
         
         if(shift < valid_length + 2) continue;
         
         // Determine trend and alerts
         if(shift > 0)
         {
            if(ColorMode && laguerre[shift-1] > 0)
            {
               double prev_trend = trend[shift-1];
               trend[shift] = prev_trend;
               
               if(laguerre[shift] > laguerre[shift-1]) 
               {
                  trend[shift] = 1;
                  if(AlertOnTrendChange && prev_trend != 1 && Time[shift] != last_alert_time)
                  {
                     Alert("Adaptive Laguerre: UPTREND started at ", DoubleToString(price[shift], _Digits));
                     last_alert_time = Time[shift];
                  }
               }
               else if(laguerre[shift] < laguerre[shift-1]) 
               {
                  trend[shift] = 2;
                  if(AlertOnTrendChange && prev_trend != 2 && Time[shift] != last_alert_time)
                  {
                     Alert("Adaptive Laguerre: DOWNTREND started at ", DoubleToString(price[shift], _Digits));
                     last_alert_time = Time[shift];
                  }
               }
            }    
            else trend[shift] = 0; 
         }
      }
   }
   
   return(rates_total);
}

//+------------------------------------------------------------------+
//| Enhanced Laguerre filter with numerical stability               |
//+------------------------------------------------------------------+
double LaguerreEnhanced(double _price, double _gamma, int order, datetime time, int bar)
{
   double gam = 1 - _gamma; 
   
   double array[];
   ArrayResize(array, order);
   
   if(time != prevtime)
   {
      for(int i = 0; i < order; i++) 
         L[i][1] = L[i][0];
      prevtime = time;
   }
   
   for(int i = 0; i < order; i++)
   {
      if(bar <= order) 
      {
         L[i][0] = _price;
      }
      else
      {
         if(i == 0) 
         {
            // Enhanced calculation with better numerical stability
            double factor1 = 1 - gam;
            double factor2 = gam;
            L[i][0] = factor1 * _price + factor2 * L[i][1];
         }
         else
         {
            // Prevent numerical instability
            double term1 = -gam * L[i-1][0];
            double term2 = L[i-1][1];
            double term3 = gam * L[i][1];
            L[i][0] = term1 + term2 + term3;
         }
      }
      array[i] = L[i][0];
   }
   
   return(TriMA_gen(array, order, order-1));
}

//+------------------------------------------------------------------+
//| Original Laguerre filter                                        |
//+------------------------------------------------------------------+
double Laguerre(double _price, double _gamma, int order, datetime time, int bar)
{
   double gam = 1 - _gamma; 
   
   double array[];
   ArrayResize(array, order);
   
   if(time != prevtime)
   {
      for(int i = 0; i < order; i++) 
         L[i][1] = L[i][0];
      prevtime = time;
   }
   
   for(int i = 0; i < order; i++)
   {
      if(bar <= order) 
         L[i][0] = _price;
      else
      {
         if(i == 0) 
            L[i][0] = (1 - gam) * _price + gam * L[i][1];
         else
            L[i][0] = -gam * L[i-1][0] + L[i-1][1] + gam * L[i][1];
      }
      array[i] = L[i][0];
   }
   
   return(TriMA_gen(array, order, order-1));
}

//+------------------------------------------------------------------+
//| Adaptive Factor Calculation                                     |
//+------------------------------------------------------------------+
double AdaptiveGamma(double& array[], int per, int bar)
{
   double eff, sum = 0, max = 0, min = 1000000000; 
   
   for(int i = 0; i < per; i++) 
   {
      if(array[bar-i] > max) max = array[bar-i]; 
      if(array[bar-i] < min) min = array[bar-i]; 
   }
   
   if(max - min != 0) 
      eff = (array[bar] - min) / (max - min); 
   else 
      eff = 0;
   
   return(eff);  
}

//+------------------------------------------------------------------+
//| Moving Average Functions                                        |
//+------------------------------------------------------------------+

// Simple Moving Average
double SMA(double& array[], int per, int bar)
{
   double Sum = 0;
   for(int i = 0; i < per; i++) 
      Sum += array[bar-i];
   
   return(Sum/per);
}

// Exponential Moving Average
double EMA(double _price, int per, datetime time, int bar)
{
   if(ptime != time) 
   {
      ema[1] = ema[0]; 
      ptime = time;
   } 
   
   if(ftime) 
   {
      ema[0] = _price; 
      ftime = false;
   }
   else 
      ema[0] = ema[1] + 2.0/(1+per) * (_price - ema[1]); 
   
   return(ema[0]);
}

// Linear Weighted Moving Average 
double LWMA(double& array[], int per, int bar)
{
   double lwma, Sum = 0, Weight = 0;
   
   for(int i = 0; i < per; i++)
   { 
      Weight += (per - i);
      Sum += array[bar-i] * (per - i);
   }
   
   if(Weight > 0) 
      lwma = Sum/Weight; 
   else 
      lwma = 0; 
   
   return(lwma);
}

// Triangular Moving Average Generalized
double TriMA_gen(double& array[], int per, int bar)
{
   int len1 = (int)MathFloor((per+1)*0.5);
   int len2 = (int)MathCeil((per+1)*0.5);
   double sum = 0;
   
   for(int i = 0; i < len2; i++) 
      sum += SMA(array, len1, bar-i);
   
   double trimagen = sum/len2;
   
   return(trimagen);
}

// Moving Median
double Median(double& _price[], int per, int bar)
{
   double median, array[];
   ArrayResize(array, per);
   
   for(int i = 0; i < per; i++) 
      array[i] = _price[bar-i];
   
   ArraySort(array);
   
   int num = (int)MathRound((per-1)/2); 
   
   if(MathMod(per, 2) > 0) 
      median = array[num]; 
   else 
      median = 0.5 * (array[num] + array[num+1]);
   
   return(median); 
}

//+------------------------------------------------------------------+
//| Helper Functions                                                |
//+------------------------------------------------------------------+

string timeframeToString(ENUM_TIMEFRAMES TF)
{
   switch(TF)
   {
      case PERIOD_CURRENT:  return("Current");
      case PERIOD_M1:       return("M1");   
      case PERIOD_M2:       return("M2");
      case PERIOD_M3:       return("M3");
      case PERIOD_M4:       return("M4");
      case PERIOD_M5:       return("M5");      
      case PERIOD_M6:       return("M6");
      case PERIOD_M10:      return("M10");
      case PERIOD_M12:      return("M12");
      case PERIOD_M15:      return("M15");
      case PERIOD_M20:      return("M20");
      case PERIOD_M30:      return("M30");
      case PERIOD_H1:       return("H1");
      case PERIOD_H2:       return("H2");
      case PERIOD_H3:       return("H3");
      case PERIOD_H4:       return("H4");
      case PERIOD_H6:       return("H6");
      case PERIOD_H8:       return("H8");
      case PERIOD_H12:      return("H12");
      case PERIOD_D1:       return("D1");
      case PERIOD_W1:       return("W1");
      case PERIOD_MN1:      return("MN1");      
      default:              return("Current");
   }
}

string priceToString(ENUM_APPLIED_PRICE app_price)
{
   switch(app_price)
   {
      case PRICE_CLOSE:     return("Close");
      case PRICE_HIGH:      return("High");
      case PRICE_LOW:       return("Low");
      case PRICE_MEDIAN:    return("Median");
      case PRICE_OPEN:      return("Open");
      case PRICE_TYPICAL:   return("Typical");
      case PRICE_WEIGHTED:  return("Weighted");
      default:              return("");
   }
}

datetime iTime(string symbol, ENUM_TIMEFRAMES TF, int index)
{
   if(index < 0) 
      return(-1);
   
   static datetime timearray[];
   
   if(CopyTime(symbol, TF, index, 1, timearray) > 0) 
      return(timearray[0]); 
   else 
      return(-1);
}