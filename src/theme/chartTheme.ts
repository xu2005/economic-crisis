import * as echarts from 'echarts/core';
import { LineChart, BoxplotChart, ScatterChart, HeatmapChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, AriaComponent, VisualMapComponent, DataZoomComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
echarts.use([LineChart, BoxplotChart, ScatterChart, HeatmapChart, VisualMapComponent, DataZoomComponent, GridComponent, TooltipComponent, LegendComponent, MarkLineComponent, AriaComponent, VisualMapComponent, DataZoomComponent, SVGRenderer]);
export const chartColors = ['#0f6cbd', '#008a85', '#b47a12', '#8b65bd'];
export { echarts };
