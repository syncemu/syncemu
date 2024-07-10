/*************************************************************************
*   版权所有(C) 2008-2013, 深圳华为技术有限公司.
*
*   文 件 名 :  hi_hkadc.h
*
*   作    者 :  z00227143
*
*   描    述 :
*
*   修改记录 :  2013年2月2日  v1.00  z00227143  创建
*************************************************************************/
#ifndef __HI_HKADC_H__
#define __HI_HKADC_H__

#ifdef __cplusplus
extern "C" {
#endif


#define BSP_HKADC_K3V3
enum HKADC_CHANNEL_ID{
    HKADC_CHANNEL_MIN = 0,
    HKADC_CHANNEL_0 = 0,
    HKADC_CHANNEL_1,
    HKADC_CHANNEL_2,
    HKADC_CHANNEL_3,
    HKADC_CHANNEL_4,
    HKADC_CHANNEL_5,
    HKADC_CHANNEL_6,
    HKADC_CHANNEL_7,
    HKADC_CHANNEL_8,
    HKADC_CHANNEL_9,
    HKADC_CHANNEL_10,
	HKADC_CHANNEL_11,
    HKADC_CHANNEL_MAX = 11, 
};


/*hardware version */
typedef enum _ehard_ware_version
{
    HW_VERSION_BIG_LOW = HKADC_CHANNEL_4,	/* big version low byte*/
	HW_VERSION_BIG_HIGH= HKADC_CHANNEL_5,	/* big version high byte*/
    HW_VERSION_PRODUCT = HKADC_CHANNEL_9,	/* sub version */
    HW_VERSION_UDP = HKADC_CHANNEL_11	/* identify udp*/ 
}hard_ware_version;


#ifdef __cplusplus
}
#endif

#endif

