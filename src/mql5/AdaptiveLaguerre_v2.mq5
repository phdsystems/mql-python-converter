//+------------------------------------------------------------------+
//|                                          AdaptiveLaguerre_v2.mq5 |
//|                                Copyright © 2012, TrendLaboratory |
//|            http://finance.groups.yahoo.com/group/TrendLaboratory |
//|                                   E-mail: igorad2003@yahoo.co.uk |
//+------------------------------------------------------------------+
#property copyright "Copyright © 2012, TrendLaboratory"
#property link      "http://finance.groups.yahoo.com/group/TrendLaboratory"


#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1

#property indicator_type1   DRAW_COLOR_LINE
#property indicator_color1  Silver,DeepSkyBlue,OrangeRed
#property indicator_width1  2

enum ENUM_SMOOTH_MODE
{
   sma,     //SMA
   ema,     //EMA
   wilder,  //Wilder
   lwma,    //LWMA
   median   //Median
};

input ENUM_TIMEFRAMES      TimeFrame            =     0;
input ENUM_APPLIED_PRICE   Price                = PRICE_CLOSE; //Apply to
input int                  Length               =    10;       //Length  
input int                  Order                =     4;       //Laguerre Filter Order 
input int                  AdaptiveMode         =     1;       //Adaptive Mode:0-off,1-on 
input int                  AdaptiveSmooth       =     5;       //Adaptive Factor Smoothing Period
input ENUM_SMOOTH_MODE     AdaptiveSmoothMode   =     4;       //Adaptive Factor Smoothing Mode
input int                  ColorMode            =     1;       //Color Mode(0-off,1-on) 



double  laguerre[];
double  trend[];
double  price[];
double  diff[];
double  gamma[];

ENUM_TIMEFRAMES  tf;
int      mtf_handle, Price_handle;
double   L[][2], mtf_laguerre[1], mtf_trend[1], ema[2];
datetime prevtime, ptime;
bool     ftime = true;
//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
void OnInit()
{
   if(TimeFrame <= Period()) tf = Period(); else tf = TimeFrame;   
//--- indicator buffers mapping 
   SetIndexBuffer(0,laguerre,        INDICATOR_DATA); PlotIndexSetInteger(0,PLOT_COLOR_INDEXES,3);
   SetIndexBuffer(1,   trend, INDICATOR_COLOR_INDEX);
   SetIndexBuffer(2,   price,INDICATOR_CALCULATIONS);
   SetIndexBuffer(3,    diff,INDICATOR_CALCULATIONS);
   SetIndexBuffer(4,   gamma,INDICATOR_CALCULATIONS);
//--- 
   PlotIndexSetInteger(0,PLOT_DRAW_BEGIN,Length+1);
//--- 
   IndicatorSetInteger(INDICATOR_DIGITS,_Digits);
//--- 
   string short_name = "AdaptiveLaguerre_v2["+timeframeToString(TimeFrame)+"]("+priceToString(Price)+","+(string)Length+","+(string)Order+","+(string)AdaptiveMode+")";
   IndicatorSetString(INDICATOR_SHORTNAME,short_name);
   PlotIndexSetString(0,PLOT_LABEL,"AdaptiveLaguerre_v2["+timeframeToString(TimeFrame)+"]");
//---
   Price_handle = iMA(NULL,TimeFrame,1,0,0,Price);
   
   if(TimeFrame > 0) mtf_handle = iCustom(NULL,TimeFrame,"AdaptiveLaguerre_v2",0,Price,Length,Order,AdaptiveMode,AdaptiveSmooth,AdaptiveSmoothMode,ColorMode);
   else
   {
   ArrayResize(L,Order);
   
   }
//--- initialization done
}
//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,const int prev_calculated,
                const datetime &Time[],
                const double   &Open[],
                const double   &High[],
                const double   &Low[],
                const double   &Close[],
                const long     &TickVolume[],
                const long     &Volume[],
                const int      &Spread[])
{
   int x, y, shift, limit, mtflimit, copied = 0;
   double sgamma = 0;
   datetime mtf_time;
   
//--- preliminary calculations
   if(prev_calculated == 0) 
   {
   limit  = 0; 
   mtflimit = rates_total - 1;
   ArrayInitialize(laguerre,EMPTY_VALUE);
   }
   else 
   {
   limit = rates_total - 1;
   mtflimit = rates_total - prev_calculated + PeriodSeconds(tf)/PeriodSeconds(Period());
   }
     
   copied = CopyBuffer(Price_handle,0,Time[rates_total-1],Time[0],price);
   
   if(copied < 0)
   {
   Print("not all prices copied. Will try on next tick Error =",GetLastError(),", copied =",copied);
   return(0);
   }

//--- the main loop of calculations
   if(tf > Period())
   { 
   ArraySetAsSeries(Time,true);   
  
      for(shift=0,y=0;shift<mtflimit;shift++)
      {
      if(Time[shift] < iTime(NULL,TimeFrame,y)) y++; 
      mtf_time = iTime(NULL,TimeFrame,y);
      
      copied = CopyBuffer(mtf_handle,0,mtf_time,mtf_time,mtf_laguerre);
      if(copied <= 0) return(0);
      x = rates_total - shift - 1;
      laguerre[x] = mtf_laguerre[0];
           
         if(ColorMode > 0)
         {
         copied = CopyBuffer(mtf_handle,1,mtf_time,mtf_time,mtf_trend);   
         if(copied <= 0) return(0);
         trend[x] = mtf_trend[0];   
         }
         else trend[x] = 0; 
      }
   }
   else
   {
      for(shift=limit;shift<rates_total;shift++)
      {
      if(shift < Length) continue;
      
      diff[shift] = MathAbs(price[shift] - laguerre[shift-1]);
      
      if(shift < 2*Length) continue;              
      
         if(AdaptiveMode > 0) 
         {
         gamma[shift] = AdaptiveGamma(diff,Length,shift);
      
            switch(AdaptiveSmoothMode)
            {
            case 1 : sgamma = EMA   (gamma[shift],AdaptiveSmooth    ,Time[shift],shift); break;
            case 2 : sgamma = EMA   (gamma[shift],2*AdaptiveSmooth-1,Time[shift],shift); break;  
            case 3 : sgamma = LWMA  (gamma       ,AdaptiveSmooth    ,shift); break;   
            case 4 : sgamma = Median(gamma       ,AdaptiveSmooth    ,shift); break; 
            default: sgamma = SMA   (gamma       ,AdaptiveSmooth    ,shift); break;
            }
         }
         else sgamma = 10.0/(Length+9);
    
      laguerre[shift] = Laguerre(price[shift],sgamma,Order,Time[shift],shift);
    
      if(shift < Length + 2) continue;
      
         if(shift > 0)
         {
         if(ColorMode > 0 && laguerre[shift-1] > 0)
            {
            trend[shift] = trend[shift-1];
            if(laguerre[shift] > laguerre[shift-1]) trend[shift] = 1;
            if(laguerre[shift] < laguerre[shift-1]) trend[shift] = 2;    
            }    
            else trend[shift] = 0; 
         }
      }
   } 
//--- done       
   return(rates_total);
}
//+------------------------------------------------------------------+
// Laguerre filter
double Laguerre(double _price,double _gamma,int order,datetime time,int bar)
{
   double gam = 1 - _gamma; 
      
   double array[];
   ArrayResize(array,order);
   
   if(time != prevtime)
   {
   for(int i=0;i<order;i++) L[i][1] = L[i][0];
   prevtime = time;
   }
   
   for(int i=0;i<order;i++)
   {
      if(bar <= order) L[i][0] = _price;
      else
      {
         if(i == 0) L[i][0] = (1 - gam)*_price + gam*L[i][1];
         else
         L[i][0] = -gam*L[i-1][0] + L[i-1][1] + gam*L[i][1];
        
      array[i] = L[i][0];
      }
   }
  
   return(TriMA_gen(array,order,order-1));
}


// SMA - Simple Moving Average
double SMA(double& array[],int per,int bar)
{
   double Sum = 0;
   for(int i = 0;i < per;i++) Sum += array[bar-i];
     
   return(Sum/per);
}                
// EMA - Exponential Moving Average
double EMA(double _price,int per,datetime time,int bar)
{
   if(ptime != time) {ema[1] = ema[0]; ptime = time;} 
   
   if(ftime) {ema[0] = _price; ftime = false;}
   else 
   ema[0] = ema[1] + 2.0/(1+per)*(_price - ema[1]); 
   
   return(ema[0]);
}

// LWMA - Linear Weighted Moving Average 
double LWMA(double& array[],int per,int bar)
{
   double lwma, Sum = 0, Weight = 0;
   
      for(int i = 0;i < per;i++)
      { 
      Weight+= (per - i);
      Sum += array[bar-i]*(per - i);
      }
   
   if(Weight>0) lwma = Sum/Weight; else lwma = 0; 
   
   return(lwma);
} 
// TriMA generalized
double TriMA_gen(double& array[],int per,int bar)
{
   int len1 = (int)MathFloor((per+1)*0.5);
   int len2 = (int)MathCeil ((per+1)*0.5);
   double sum=0;
   for(int i = 0;i < len2;i++) sum += SMA(array,len1,bar-i);
   double trimagen = sum/len2;
   
   return(trimagen);
}

// Median - Moving Median
double Median(double& _price[],int per,int bar)
{
   double median, array[];
   ArrayResize(array,per);
   
   for(int i = 0; i < per;i++) array[i] = _price[bar-i];
   ArraySort(array);
   
   int num = (int)MathRound((per-1)/2); 
   if(MathMod(per,2)>0) median = array[num]; else median = 0.5*(array[num]+array[num+1]);
   
   return(median); 
}

// Adaptive Factor
double AdaptiveGamma(double& array[],int per,int bar)
{
   double eff, sum = 0, max = 0, min = 1000000000; 
   for(int i = 0;i < per;i++) 
   {
   if(array[bar-i] > max) max = array[bar-i]; 
   if(array[bar-i] < min) min = array[bar-i]; 
   }
      
   if(max-min != 0) eff = (array[bar] - min)/(max - min); else eff = 0;
   
   return(eff);  
} 



string timeframeToString(ENUM_TIMEFRAMES TF)
{
   switch(TF)
   {
   case PERIOD_CURRENT  : return("Current");
   case PERIOD_M1       : return("M1");   
   case PERIOD_M2       : return("M2");
   case PERIOD_M3       : return("M3");
   case PERIOD_M4       : return("M4");
   case PERIOD_M5       : return("M5");      
   case PERIOD_M6       : return("M6");
   case PERIOD_M10      : return("M10");
   case PERIOD_M12      : return("M12");
   case PERIOD_M15      : return("M15");
   case PERIOD_M20      : return("M20");
   case PERIOD_M30      : return("M30");
   case PERIOD_H1       : return("H1");
   case PERIOD_H2       : return("H2");
   case PERIOD_H3       : return("H3");
   case PERIOD_H4       : return("H4");
   case PERIOD_H6       : return("H6");
   case PERIOD_H8       : return("H8");
   case PERIOD_H12      : return("H12");
   case PERIOD_D1       : return("D1");
   case PERIOD_W1       : return("W1");
   case PERIOD_MN1      : return("MN1");      
   default              : return("Current");
   }
}

string priceToString(ENUM_APPLIED_PRICE app_price)
{
   switch(app_price)
   {
   case PRICE_CLOSE   :    return("Close");
   case PRICE_HIGH    :    return("High");
   case PRICE_LOW     :    return("Low");
   case PRICE_MEDIAN  :    return("Median");
   case PRICE_OPEN    :    return("Open");
   case PRICE_TYPICAL :    return("Typical");
   case PRICE_WEIGHTED:    return("Weighted");
   default            :    return("");
   }
}

datetime iTime(string symbol,ENUM_TIMEFRAMES TF,int index)
{
   if(index < 0) return(-1);
   static datetime timearray[];
   if(CopyTime(symbol,TF,index,1,timearray) > 0) return(timearray[0]); else return(-1);
}