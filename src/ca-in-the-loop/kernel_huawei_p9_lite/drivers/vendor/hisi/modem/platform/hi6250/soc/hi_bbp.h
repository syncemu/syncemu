

#ifndef __HI_BBP_H__
#define __HI_BBP_H__

#include "mdrv_public.h"


#ifdef __cplusplus
extern "C" {
#endif

/*各芯片平台都需要提供*/
#define BBP_CLK_MIN 0/*所有时钟阈的id*/
#define BBP_CLK_MAX 40/*所有时钟阈的id*/
#define BBP_PWR_MIN 0/*所有电源阈的id*/
#define BBP_PWR_MAX 7/*所有电源阈的id*/

#define BBP_VOTE_CLK_MIN 0   /*参与低功耗上下电的clk id*/
#define BBP_VOTE_CLK_MAX 40/*参与低功耗上下电的clk id*/
#define BBP_VOTE_PWR_MIN 0/*参与低功耗上下电的pwr id*/
#define BBP_VOTE_PWR_MAX 3/*参与低功耗上下电的pwr id*/

#define BBP_PWC_MODULE_MIN   PWC_COMM_MODULE_BBP_DRX
#define BBP_PWC_MODULE_MAX   PWC_COMM_MODULE_BBP_DBG
#define BBP_PWC_MODEM_MIN    PWC_COMM_MODEM_0
#define BBP_PWC_MODEM_MAX    PWC_COMM_MODEM_1
#define BBP_PWC_MODE_MIN     PWC_COMM_MODE_GSM
#define BBP_PWC_MODE_MAX     PWC_COMM_MODE_CDMA_HRPD

#define BBP_PWR_NUM      (BBP_PWR_MAX-BBP_PWR_MIN+1)
#define BBP_CLK_NUM      (BBP_CLK_MAX-BBP_CLK_MIN+1)
#define BBP_VOTE_PWR_NUM (BBP_VOTE_PWR_MAX-BBP_VOTE_PWR_MIN+1)
#define BBP_VOTE_CLK_NUM (BBP_VOTE_CLK_MAX-BBP_VOTE_CLK_MIN+1)
#define BBP_MODULE_NUM   (BBP_PWC_MODULE_MAX-BBP_PWC_MODULE_MIN+1)
#define BBP_MODEM_NUM    (BBP_PWC_MODEM_MAX-BBP_PWC_MODEM_MIN+1)
#define BBP_MODE_NUM     (BBP_PWC_MODE_MAX-BBP_PWC_MODE_MIN+1)

#define BBP_DMA_FIFO_BUG /*for DTS2016012906877 只有Dallas、chicago、V7R5、V722*/
#define BBP_DMA_CLK_ID 40
#ifdef __cplusplus
}
#endif

#endif

