/* Q044 component replay: unchanged pinned function bodies, local wrapper. */
#include <stdlib.h>
#include <stdio.h>
typedef char ErrorMsg[2048];
#define _FAILURE_ 1
#define _SUCCESS_ 0
#define _SPLINE_NATURAL_ 0
#define _SPLINE_EST_DERIV_ 1
#define class_test(cond,errmsg,...) do { if(cond){snprintf(errmsg,2048,__VA_ARGS__);return _FAILURE_;} } while(0)
int array_spline_table_line_to_line(
				    double * x, /* vector of size x_size */
				    int n_lines,
				    double * array,
				    int n_columns,
				    int index_y,
				    int index_ddydx2,
				    short spline_mode,
				    ErrorMsg errmsg) {

  int i,k;
  double p,qn,sig,un;
  double * u;
  double dy_first;
  double dy_last;

  class_test(n_lines<3,
             errmsg,
             "no possible spline with less than three lines");

  u = malloc((n_lines-1) * sizeof(double));
  if (u == NULL) {
    sprintf(errmsg,"%s(L:%d) Cannot allocate u",__func__,__LINE__);
    return _FAILURE_;
  }

  if (spline_mode == _SPLINE_NATURAL_) {
    *(array+0*n_columns+index_ddydx2) = u[0] = 0.0;
  }
  else {
    if (spline_mode == _SPLINE_EST_DERIV_) {
      dy_first =
	((x[2]-x[0])*(x[2]-x[0])*
	 (*(array+1*n_columns+index_y)-*(array+0*n_columns+index_y))-
	 (x[1]-x[0])*(x[1]-x[0])*
	 (*(array+2*n_columns+index_y)-*(array+0*n_columns+index_y)))/
	((x[2]-x[0])*(x[1]-x[0])*(x[2]-x[1]));
      *(array+0*n_columns+index_ddydx2) = -0.5;
      u[0] =
	(3./(x[1] -  x[0]))*
	((*(array+1*n_columns+index_y) -  *(array+0*n_columns+index_y))/
	 (x[1] - x[0])-dy_first);
    }
    else {
      sprintf(errmsg,"%s(L:%d) Spline mode not identified: %d",__func__,__LINE__,spline_mode);
      return _FAILURE_;
    }
  }

  for (i=1; i < n_lines-1; i++) {

      sig = (x[i] - x[i-1]) / (x[i+1] - x[i-1]);

      p = sig * *(array+(i-1)*n_columns+index_ddydx2) + 2.0;
      *(array+i*n_columns+index_ddydx2) = (sig-1.0)/p;
      u[i] = (*(array+(i+1)*n_columns+index_y) - *(array+i*n_columns+index_y))
	/ (x[i+1] - x[i])
	- (*(array+i*n_columns+index_y) - *(array+(i-1)*n_columns+index_y))
	/ (x[i] - x[i-1]);
      u[i]= (6.0 * u[i] /
	     (x[i+1] - x[i-1])
	     - sig * u[i-1]) / p;

  }

  if (spline_mode == _SPLINE_NATURAL_) {
    qn=0.;
    un=0.;
  }
  else {
    if (spline_mode == _SPLINE_EST_DERIV_) {
      dy_last =
	((x[n_lines-3]-x[n_lines-1])*(x[n_lines-3]-x[n_lines-1])*
	 (*(array+(n_lines-2)*n_columns+index_y)-*(array+(n_lines-1)*n_columns+index_y))-
	 (x[n_lines-2]-x[n_lines-1])*(x[n_lines-2]-x[n_lines-1])*
	 (*(array+(n_lines-3)*n_columns+index_y)-*(array+(n_lines-1)*n_columns+index_y)))/
	((x[n_lines-3]-x[n_lines-1])*(x[n_lines-2]-x[n_lines-1])*(x[n_lines-3]-x[n_lines-2]));
      qn=0.5;
      un =
	(3./(x[n_lines-1] - x[n_lines-2]))*
	(dy_last-(*(array+(n_lines-1)*n_columns+index_y) -  *(array+(n_lines-2)*n_columns+index_y))/
	 (x[n_lines-1] - x[n_lines-2]));
    }
    else {
      sprintf(errmsg,"%s(L:%d) Spline mode not identified: %d",__func__,__LINE__,spline_mode);
      return _FAILURE_;
    }
  }

  *(array+(n_lines-1)*n_columns+index_ddydx2) =
    (un-qn*u[n_lines-2])/(qn* *(array+(n_lines-2)*n_columns+index_ddydx2)+1.0);

  for (k=n_lines-2; k>=0; k--)
    *(array+k*n_columns+index_ddydx2) = *(array+k*n_columns+index_ddydx2) *
      *(array+(k+1)*n_columns+index_ddydx2) + u[k];

  free(u);

  return _SUCCESS_;
 }
int array_integrate_all_spline_table_line_to_line(
                  double * x_array,
                  int n_lines,
                  double * array,
                  int n_columns,
                  int index_y,
                  int index_ddy,
                  double * result,
                  ErrorMsg errmsg){

  int i;
  double h;

  *result = 0;

  for (i=0; i < n_lines-1; i++) {

    h = (x_array[i+1]-x_array[i]);

    *result +=
      (array[i*n_columns+index_y]+array[(i+1)*n_columns+index_y])*h/2.+
      (array[i*n_columns+index_ddy]+array[(i+1)*n_columns+index_ddy])*h*h*h/24.;

  }

  return _SUCCESS_;
}
double q044_replay(double *x,double *y,int n){
 double *a=calloc(n*2,sizeof(double));ErrorMsg e;double r;
 if(!a)return 0.0/0.0;
 for(int i=0;i<n;i++)a[i*2]=y[i];
 int status=array_spline_table_line_to_line(x,n,a,2,0,1,_SPLINE_EST_DERIV_,e);
 if(!status)status=array_integrate_all_spline_table_line_to_line(x,n,a,2,0,1,&r,e);
 free(a);return status?0.0/0.0:-r;
}
