/******************************************************************************

                  ��Ȩ���� (C), 2001-2011, ��Ϊ�������޹�˾

 ******************************************************************************
  �� �� ��   : CnasXregRegingProcTbl.h
  �� �� ��   : ����
  ��    ��   : y00245242
  ��������   : 2014��7��3��
  ����޸�   :
  ��������   : CnasXregRegingProcTbl.c ��ͷ�ļ�
  �����б�   :
  �޸���ʷ   :
  1.��    ��   : 2014��7��3��
    ��    ��   : y00245242
    �޸�����   : �����ļ�

******************************************************************************/

#ifndef __CNAS_XREG_REGING_PROC_TBL_H__
#define __CNAS_XREG_REGING_PROC_TBL_H__

/*****************************************************************************
  1 ����ͷ�ļ�����
*****************************************************************************/
#include  "vos.h"
#include  "NasFsm.h"
#include  "cas_1x_access_ctrl_proc_nas_pif.h"

#ifdef __cplusplus
#if __cplusplus
extern "C" {
#endif
#endif


#pragma pack(4)

/*****************************************************************************
  2 ȫ�ֱ�������
*****************************************************************************/
extern NAS_STA_STRU     g_astCnasXsdSwitchOnStaTbl[];

extern NAS_STA_STRU     g_astCnasXregRegingStaTbl[];

/*****************************************************************************
  3 �궨��
*****************************************************************************/
#define CNAS_XREG_GetRegingStaTbl()                        (g_astCnasXregRegingStaTbl)

/*****************************************************************************
  4 ö�ٶ���
*****************************************************************************/
/*****************************************************************************
 ö����    : CNAS_XREG_REGING_STA_ENUM_UINT32
 ö��˵��  : ����״̬��IDö�ٶ���
 1.��    ��   : 2014��07��03��
   ��    ��   : h00246512
   �޸�����   : �½�
*****************************************************************************/
enum CNAS_XREG_REGING_STA_ENUM
{
    /* ע����״̬������ʼ״̬ */
    CNAS_XREG_REGING_STA_INIT                = 0x00,

    /* ע����״̬�����ȴ�ע��ظ�״̬ */
    CNAS_XREG_REGING_WAIT_EST_CNF            = 0x01,

    /* ע����״̬�����ȴ���ֹ�ظ�״̬ */
    CNAS_XREG_REGING_WAIT_ABORT_IND          = 0x02,

    CNAS_XREG_REGING_STA_BUTT
};
typedef VOS_UINT32 CNAS_XREG_REGING_STA_ENUM_UINT32;

/*****************************************************************************
  5 ��Ϣͷ����
*****************************************************************************/


/*****************************************************************************
  6 ��Ϣ����
*****************************************************************************/


/*****************************************************************************
  7 STRUCT����
*****************************************************************************/


/*****************************************************************************
  8 UNION����
*****************************************************************************/


/*****************************************************************************
  9 OTHERS����
*****************************************************************************/


/*****************************************************************************
  10 ��������
*****************************************************************************/
#if (FEATURE_ON == FEATURE_UE_MODE_CDMA)
extern VOS_UINT32  CNAS_XREG_RcvRegReq_Reging_Init(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32  CNAS_XREG_RcvAbortFsm_Reging_WaitEstCnf(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32  CNAS_XREG_RcvEstCnf_Reging_WaitEstCnf(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32  CNAS_XREG_RcvAbortInd_Reging_WaitEstCnf(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32  CNAS_XREG_RcvTimeOut_Reging_WaitEstCnf(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32  CNAS_XREG_RcvAbotInd_Reging_WaitAbortInd(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32  CNAS_XREG_RcvTimeOut_Reging_WaitAbortInd(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32 CNAS_XSD_GetSwitchOnStaTblSize(VOS_VOID);

extern NAS_FSM_DESC_STRU * CNAS_XREG_GetRegingFsmDescAddr(VOS_VOID);

extern VOS_UINT32 CNAS_XREG_GetRegingStaTblSize(VOS_VOID);

extern NAS_FSM_DESC_STRU * CNAS_XSD_GetSwitchOnFsmDescAddr(VOS_VOID);

extern VOS_UINT32  CNAS_XREG_RcvAbortInd_Reging_WaitAbortInd(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

extern VOS_UINT32  CNAS_XREG_PostProcessMsg_Reging(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);
extern VOS_UINT32 CNAS_XREG_IsNeedNotifyApsRegBegin(
    CAS_CNAS_1X_REGISTRATION_TYPE_ENUM_UINT8                enRegType
);

extern VOS_UINT32  CNAS_XREG_RcvPwrOffTimeOut_Reging_WaitEstCnf(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
);

#endif



#if (VOS_OS_VER == VOS_WIN32)
#pragma pack()
#else
#pragma pack(0)
#endif




#ifdef __cplusplus
    #if __cplusplus
        }
    #endif
#endif

#endif /* end of CnasXsdFsmSwitchOnTbl.h */

