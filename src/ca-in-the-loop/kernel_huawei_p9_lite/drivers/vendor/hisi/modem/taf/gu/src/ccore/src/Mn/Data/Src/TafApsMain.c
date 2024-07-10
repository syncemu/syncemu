
/******************************************************************************

                  ��Ȩ���� (C), 2001-2011, ��Ϊ�������޹�˾

 ******************************************************************************
  �� �� ��   : TafApsMain.c
  �� �� ��   : ����
  ��    ��   : S62952
  ��������   : 2011��12��14��
  ����޸�   :
  ��������   : ����Ϣ��ڴ���������ȫ�ֱ����ĳ�ʼ����Ԥ��������Ϣ���,
               ״̬�������Ϣ
  �����б�   :

  �޸���ʷ   :
  1.��    ��   : 2011��12��14��
    ��    ��   : S62952
    �޸�����   : �����ļ�

******************************************************************************/

/*****************************************************************************
  1 ͷ�ļ�����
*****************************************************************************/
#include "TafFsm.h"
#include "TafApsCtx.h"
#include "TafApsMain.h"
#include "TafApsPreProcTbl.h"
#include "TafApsFsmMainTbl.h"
#include "TafApsFsmMsActivatingTbl.h"
#include "TafApsFsmNwActivatingTbl.h"
#include "TafApsFsmMsDeactivatingTbl.h"
#include "TafApsFsmMsModifyingTbl.h"
#include "TafLog.h"
#include "PsCommonDef.h"
#include "TafApsGetPdpIdList.h"
#include "TafApsProcIpFilter.h"
#include "TafApsFsmCdataEstingTbl.h"
#include "TafApsFsmCdataDiscingTbl.h"
#include "TafApsMntn.h"
#include "TafApsFsmCdataHandOffTbl.h"


#ifdef __cplusplus
#if __cplusplus
    extern "C" {
#endif
#endif

/*lint -e958*/

/*****************************************************************************
    Э��ջ��ӡ��㷽ʽ�µ�.C�ļ��궨��
*****************************************************************************/
#define    THIS_FILE_ID        PS_FILE_ID_TAF_APS_MAIN_C

/******************************************************************************
   2 �ⲿ������������
******************************************************************************/

/******************************************************************************
   3 ˽�ж���
******************************************************************************/


/******************************************************************************
   4 ȫ�ֱ�������
*****************************************************************************/


/******************************************************************************
   5 ����ʵ��
******************************************************************************/
/*****************************************************************************
 �� �� ��  : TAF_APS_RegMainFsm
 ��������  : APS Main״̬������״̬��ע��
 �������  : ��
 �������  : ��
 �� �� ֵ  : ��
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��16��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID TAF_APS_RegMainFsm( VOS_VOID  )
{
    /* ״̬��ע�� */

    TAF_FSM_RegisterFsm((TAF_APS_GetMainFsmDescAddr()),
                         "TAF:FSM:APS:MAIN",
                         (VOS_UINT32)(TAF_APS_GetMainFsmStaTblSize()),
                         TAF_APS_GetMainFsmStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);
    return;
}

/*****************************************************************************
 �� �� ��  : TAF_APS_RegSubFsm
 ��������  : Sub״̬������״̬��ע��
 �������  : ��
 �������  : ��
 �� �� ֵ  : ��
 ���ú���  :
 ��������  :

 �޸���ʷ      :
 1.��    ��   : 2011��12��16��
   ��    ��   : h44270
   �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID TAF_APS_RegSubFsm( VOS_VOID  )
{

    /* MS ACTIVATING״̬��ע�� */
    TAF_FSM_RegisterFsm((TAF_APS_GetMsActivatingFsmDescAddr()),
                         "TAF:FSM:APS:Ms Activating",
                         (VOS_UINT32)TAF_APS_GetMsActivatingStaTblSize(),
                         TAF_APS_GetMsActivatingStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);


    /* NW ACTIVATING״̬��ע�� */
    TAF_FSM_RegisterFsm((TAF_APS_GetNwActivatingFsmDescAddr()),
                         "TAF:FSM:APS:Nw Activating",
                         (VOS_UINT32)TAF_APS_GetNwActivatingStaTblSize(),
                         TAF_APS_GetNwActivatingStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);

    /*MS DEACTIVATING״̬��ע�� */
    TAF_FSM_RegisterFsm((TAF_APS_GetMsDeactivatingFsmDescAddr()),
                         "TAF:FSM:APS:MS Deactivating",
                         (VOS_UINT32)TAF_APS_GetMsDeactivatingStaTblSize(),
                         TAF_APS_GetMsDeactivatingStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);

    /* MS MODIFYING״̬��ע�� */
    TAF_FSM_RegisterFsm((TAF_APS_GetMsModifyingFsmDescAddr()),
                         "TAF:FSM:APS:Ms Modifying",
                         (VOS_UINT32)TAF_APS_GetMsModifyingStaTblSize(),
                         TAF_APS_GetMsModifyingStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);

#if (FEATURE_ON == FEATURE_UE_MODE_CDMA)

    /* CDATA ESTING״̬��ע�� */
    TAF_FSM_RegisterFsm((TAF_APS_GetCdataEstingFsmDescAddr()),
                         "TAF:FSM:APS:CDATA ESTING",
                         (VOS_UINT32)TAF_APS_GetCdataEstingStaTblSize(),
                         TAF_APS_GetCdataEstingStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);

    /* CDATA DISCING״̬��ע�� */
    TAF_FSM_RegisterFsm((TAF_APS_GetCdataDiscingFsmDescAddr()),
                         "TAF:FSM:APS:CDATA DISCING",
                         (VOS_UINT32)TAF_APS_GetCdataDiscingStaTblSize(),
                         TAF_APS_GetCdataDiscingStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);
    /* CDATA HANDOFF״̬��ע�� */
    TAF_FSM_RegisterFsm((TAF_APS_GetCdataHandOffFsmDescAddr()),
                         "TAF:FSM:APS:CDATA HANDOFF",
                         (VOS_UINT32)TAF_APS_GetCdataHandOffStaTblSize(),
                         TAF_APS_GetCdataHandOffStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);

#endif

    return;
}

/*****************************************************************************
 �� �� ��  : TAF_APS_RegPreFsm
 ��������  : APSԤ����״̬��ע��
 �������  : ��
 �������  : ��
 �� �� ֵ  : ��
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��19��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID TAF_APS_RegPreFsm( VOS_VOID  )
{
    /* Ԥ����ע�� */

    TAF_FSM_RegisterFsm((TAF_APS_GetPreFsmDescAddr()),
                         "NAS:FSM:MMC:PreProcess",
                         TAF_APS_GetPreProcessStaTblSize(),
                         TAF_APS_GetPreProcessStaTbl(),
                         VOS_NULL_PTR,
                         VOS_NULL_PTR);
    return;
}

/*****************************************************************************
 �� �� ��  : TAF_APS_InitTask
 ��������  : APS��ʼ������
 �������  : ��
 �������  : ��
 �� �� ֵ  :
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��19��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

  2.��    ��   : 2015��2��12��
    ��    ��   : A00165503
    �޸�����   : DTS2015022600839: ���������ĳ�ʼ���ŵ������ʼ��������

  3.��    ��   : 2016��7��2��
    ��    ��   : w00316404
    �޸�����   : DTS2016062907860: IMSA�����IMS���ؼ���������Ҫ��AttachĬ�ϳ��ؼ���֮���ٷ���
*****************************************************************************/
VOS_VOID  TAF_APS_InitTask( VOS_VOID )
{

    /* ��ʼ��APSģ��CTX */
    TAF_APS_InitCtx();

    /* ��ʼ��APS����ͳ�������� */
    TAF_APS_InitDsFlowCtx(TAF_APS_GetDsFlowCtxAddr());

    /* ��ʼ��DDR��Ƶ��Ϣ */
    TAF_APS_InitSwitchDdrInfo();

    TAF_APS_InitAttachBearerReestInfo();

    /*ע��״̬��*/
    TAF_APS_RegFsm();

    return;
}
/*****************************************************************************
 �� �� ��  : TAF_APS_InitEntityFsm
 ��������  : ʵ��״̬���ĳ�ʼ��
 �������  : ��
 �������  : ��
 �� �� ֵ  : ��
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2012��1��28��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

  2.��    ��   : 2012��6��27��
    ��    ��   : A00165503
    �޸�����   : DTS2012062608382: APS��ʼ��PS��״̬Ϊ��Ч, ���MMC��֪ͨ-
                 APS�ĳ����·���PDP����ʧ��
*****************************************************************************/
VOS_VOID  TAF_APS_InitEntityFsm( VOS_VOID )
{
    VOS_UINT8                           i;
    TAF_APS_PDP_ENTITY_FSM_CTX_STRU    *pstCurrPdpEntityFsm;

    /* for ѭ������ʼ������ʵ��״̬�������ģ�������״̬������״̬�� */
    for (i = 0; i < TAF_APS_MAX_PDPID; i++)
    {
        /* �������õ�ǰ��ʵ��״̬�� */
        TAF_APS_SetCurrPdpEntityFsmAddr(i);
        pstCurrPdpEntityFsm = TAF_APS_GetCurrPdpEntityFsmAddr();

        /* ��ʼ��ʵ�������� */
        TAF_APS_InitMainFsmCtx(&pstCurrPdpEntityFsm->stMainFsm);
        TAF_APS_InitSubFsmCtx(&pstCurrPdpEntityFsm->stSubFsm);

        pstCurrPdpEntityFsm->ucPdpId = TAF_APS_INVALID_PDPID;                       /* ��ǰ״̬������Ӧ��PDP ID */

        pstCurrPdpEntityFsm->ucCallActiveFlg = VOS_FALSE;
    }

}
/*****************************************************************************
 �� �� ��  : TAF_APS_InitCtx
 ��������  : APS CTXģ���ʼ��
 �������  :
 �������  :
 �� �� ֵ  :
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2012��12��16��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

  2.��    ��   : 2012��06��16��
    ��    ��   : m00217266
    �޸�����   : ����PDP�������������ĳ�ʼ��(AT&T&DCM���� PDP��������)

  3.��    ��   : 2014��2��20��
    ��    ��   : A00165503
    �޸�����   : DTS2013022201185: ���Ӻ��н���������ʱ��ʱ����ʼ��

  4.��    ��   : 2014��11��1��
    ��    ��   : A00165503
    �޸�����   : DTS2014122908593: ����PDN���ӶϿ����Գ�ʼ��

  5.��    ��   : 2015��2��12��
    ��    ��   : A00165503
    �޸�����   : DTS2015022600839: ���������ĳ�ʼ���ŵ������ʼ��������
*****************************************************************************/
VOS_VOID  TAF_APS_InitCtx( VOS_VOID )
{
    TAF_APS_CONTEXT_STRU               *pApsCtx;

    /* ��ʼ��APSģ��CTX */
    pApsCtx   = TAF_APS_GetApsCtxAddr();

    /* ��ʼ�����е�ʵ��״̬�� */
    TAF_APS_InitEntityFsm();

    /* ��ʼ���ڲ�������� */
    TAF_APS_InitInternalBuffer(TAF_APS_GetCachMsgBufferAddr());

    /* ��ʼ��APS��ʱ�������� */
    TAF_APS_InitAllTimers(TAF_APS_GetTimerCtxAddr());


    /* ��ʼ���ڲ���Ϣ���� */
    TAF_APS_InitInternalMsgQueue(&pApsCtx->stInternalMsgQueue);

    /* ��ʼ��AT�������� */
    TAF_APS_InitCmdBufferQueue(TAF_APS_GetCmdBufferQueueAddr());

    /* ��ʼ������NDIS Filter��Ч */
    TAF_APS_SetUlNdisFilterValidFlag(TAF_APS_UL_NDIS_FILTER_VALID);

    /* ��ʼ������NDIS��Ҫʹ�õ�IP Filter���� */
    TAF_APS_IpfUlNdisFilterInit();

    /* ��ʼ��PDP�������ޱ�־����PDP����ʧ�ܴ��������� */
    TAF_APS_InitPdpActLimitInfo();

    /* ��ʼ�����б�����ʱ��ʱ�� */
    TAF_APS_InitCallRemainTmrLen();

    TAF_APS_SET_RAT_TYPE_IN_SUSPEND(TAF_APS_RAT_TYPE_NULL);

    TAF_APS_SetCurrPdpEntityRatType(TAF_APS_RAT_TYPE_NULL);
    TAF_APS_SetCurrPdpEntitySimRegStatus(VOS_TRUE);
    /* ���õ�ǰPSҵ�����ڵ�ģʽ */
    TAF_APS_SetCurrPdpEntityDataServiceMode(TAF_APS_RAT_TYPE_NULL);

#if (FEATURE_ON == FEATURE_LTE)
    /* ��ʼ��PDN���ӶϿ�����������Ϣ */
    TAF_APS_InitPdnTeardownPolicy();
#endif

#if (FEATURE_ON == FEATURE_UE_MODE_CDMA)
    TAF_APS_Set1XPsServiceStatus(VOS_FALSE);
    TAF_APS_SetClDelaySearch(VOS_TRUE);
    TAF_APS_SetIsHrpdDisabledFlag(VOS_FALSE);

    TAF_APS_InitCdataCtx();
    TAF_APS_Init3GpdOpInfo();
    g_stTafApsCtx.ulIsAlreadyRead3GpdFile = VOS_FALSE;
    g_stTafApsCtx.ulReadSim3GpdFileFlg      = TAF_APS_READ_USIM_FILE_FLG_NULL;
#endif

    return;
}

/*****************************************************************************
 �� �� ��  : TAF_APS_RegFsm
 ��������  : ע��״̬��
 �������  : ��
 �������  : ��
 �� �� ֵ  :
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��16��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID  TAF_APS_RegFsm( VOS_VOID )
{
    /* ע��Ԥ����״̬�� */
    TAF_APS_RegPreFsm();

    /* ע����״̬�� */
    TAF_APS_RegMainFsm();

    /* ע����״̬�� */
    TAF_APS_RegSubFsm();

}

/*****************************************************************************
 �� �� ��    : TAF_APS_FSM_ProcessEvent
 ��������    : ״̬�����¼���������
 �������    :
               ulCurState :��ǰ״̬
               ulEventType:�����¼�
               ulMsgID    :��ϢID
               pRcvMsg    :��Ϣָ��
               pstFsmDesc :״̬��������
 �������    :
 ����ֵ      : VOS_UINT32:�����Ƿ����
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��17��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

 *****************************************************************************/
VOS_UINT32 TAF_APS_FSM_ProcessEvent(
    VOS_UINT32                          ulCurState,
    VOS_UINT32                          ulEventType,
    VOS_VOID                           *pRcvMsg,
    TAF_FSM_DESC_STRU                  *pstFsmDesc
)
{
    TAF_ACTION_FUNC                     pActFun;
    VOS_UINT32                          ulRet;

    TAF_INFO_LOG2(WUEPS_PID_TAF,"TAF_APS_FSM_ProcessEvent", ulCurState, ulEventType);

    /* ����״̬ת�Ʊ��е���Ӧ�Ķ����������� */
    pActFun = TAF_FSM_FindAct(pstFsmDesc, ulCurState, ulEventType);

    if (VOS_NULL_PTR != pActFun )
    {
        /* ������ص��¼�����������Ϊ��,�����������¼����� */
        ulRet   = (*pActFun) ( ulEventType,(struct MsgCB*)pRcvMsg);
        TAF_INFO_LOG1(WUEPS_PID_TAF,"TAF_APS_FSM_ProcessEvent", ulRet);
        return VOS_TRUE;
    }

    /* ��Ϣδ������������������ */
    return VOS_FALSE;
}


/*****************************************************************************
 �� �� ��  : TAF_APS_ProcessBufferMsg
 ��������  : ��������
 �������  : ��
 �������  : ��
 �� �� ֵ  :
 ���ú���  :
 ��������  :

 �޸���ʷ      :
 1.��    ��   : 2011��12��16��
   ��    ��   : h44270
   �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID TAF_APS_ProcessBufferMsg(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
)
{
    /* ��ǰ��ʵ�ֻ����£������л�����Ϣ�����ֻ�����˺����Ŀ�ܣ�
       ��������Ҫ��ʱ���ٽ������� */

    return;
}



/*****************************************************************************
 �� �� ��  : TAF_APS_PostProcessMsg
 ��������  : APS״̬����������,����ǰ�յ�����Ϣ���л�����߶����Ĵ���
 �������  : ulEventType:��Ϣ����
             pstMsg       :��Ϣ����
 �������  : ��
 �� �� ֵ  : ��
 ���ú���  :
 ��������  :

 �޸���ʷ      :
 1.��    ��   : 2011��12��16��
   ��    ��   : h44270
   �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID  TAF_APS_PostProcessMsg(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
)
{
    /* ����ǰ����Ϣ���л��� */
    /* ��ǰӦ�ò�����ֻ�����Ҫ����˴�����ע�͵�����������״̬������������Ϣ��
       �����ж��� */
    return;
}


/*****************************************************************************
 �� �� ��  : TAF_APS_MsgPreProcess
 ��������  : MMC��ϢԤ����
 �������  : ulEventType:��Ϣ����
              pMsg       :��Ϣ����
 �������  : ��
 �� �� ֵ  : VOS_TRUE:Ԥ�������
              VOS_FALSE:����Ҫ����״̬���д���
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��16��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

*****************************************************************************/
VOS_UINT32 TAF_APS_PreProcessMsg(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
)
{
    TAF_ACTION_FUNC                     pActFun;
    TAF_FSM_DESC_STRU                  *pstFsmDesc;
    VOS_UINT32                          ulRet;

    /* ��ϢԤ���� */

    TAF_INFO_LOG1(WUEPS_PID_TAF,"TAF_APS_PreProcessMsg", (VOS_INT32)ulEventType);

    pstFsmDesc = TAF_APS_GetPreFsmDescAddr();

    /* ����״̬ת�Ʊ��е���Ӧ�Ķ����������� */
    pActFun = TAF_FSM_FindAct(pstFsmDesc, TAF_APS_STA_PREPROC, ulEventType);

    if (VOS_NULL_PTR != pActFun )
    {
        /* Ԥ������Ϣ,��Ϊ������Ϣ,һ��ΪԤ���������ͷ���,����һ��ΪԤ����
        ������,��Ȼ��Ҫ���е�״̬���м�������,��˴˴�ֱ��ͨ����������Ԥ��
        ���������Ƿ���Ҫ����״̬������*/
        ulRet = (*pActFun) ( ulEventType, pstMsg);
        return ulRet;
    }

    /* ��Ϣδ������������������ */
    return VOS_FALSE;
}


/*****************************************************************************
 �� �� ��  : TAF_APS_ProcessMsgInFsm
 ��������  : ��Ϣ״̬������
 �������  : ulEventType :  ��Ϣ����+PID
              pMsg        :  ��Ϣ����
 �������  : ��
 �� �� ֵ  : VOS_TRUE:����Ϣ�Ƿ������
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��16��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

*****************************************************************************/
VOS_UINT32 TAF_APS_ProcessMsgInFsm(
    VOS_UINT32                          ulEventType,
    struct MsgCB                       *pstMsg
)
{
    VOS_UINT32                          ulRet;
    TAF_APS_PDP_ENTITY_FSM_CTX_STRU    *pstCurPdpEntityFsmCtx;
    VOS_UINT8                           i;
    TAF_APS_FSM_ID_ENUM_UINT32          enPreSubFsmId;
    TAF_APS_PDPID_LIST_STRU             stPdpIdList;
    /* ��ά�ɲ⣬����ǰ����״̬��״̬ */
    TAF_APS_FSM_STATUS_INFO_STRU        stPriFsmInfo;
    TAF_APS_FSM_STATUS_INFO_STRU        stCurrFsmInfo;

    /* �����Ҫ�ͳ���PDP�����б��ı���pstPdpIdList */
    PS_MEM_SET(&stPdpIdList, 0, sizeof(TAF_APS_PDPID_LIST_STRU));

    /* ��ȡ��Ҫ������Pdp �б� */
    TAF_APS_GetFsmPdpIdList(ulEventType, pstMsg, &stPdpIdList);

    ulRet = VOS_FALSE;

    for (i = 0; i < stPdpIdList.ucPdpNum; i++)
    {
        /* ����PDP ID�����õ�ǰ��ʵ��״̬�� */
        TAF_APS_SetCurrPdpEntityFsmAddr(stPdpIdList.aucPdpId[i]);

        /* ���õ�ǰ״̬��ʵ���PDP ID */
        TAF_APS_SetCurrFsmEntityPdpId(stPdpIdList.aucPdpId[i]);

        /* ��ά�ɲ⣬��ӡ��ǰPDPʵ����Ϣ */
        TAF_APS_LogPdpEntityInfo(stPdpIdList.aucPdpId[i]);

        PS_MEM_SET(&stPriFsmInfo, 0xFF, sizeof(TAF_APS_FSM_STATUS_INFO_STRU));
        PS_MEM_SET(&stCurrFsmInfo, 0xFF, sizeof(TAF_APS_FSM_STATUS_INFO_STRU));

        pstCurPdpEntityFsmCtx = TAF_APS_GetCurrPdpEntityFsmAddr();

        /* �����ǰ��״̬���Ѿ����ڣ���ֱ�ӽ��뵽��״̬������ */
        if (TAF_APS_FSM_BUTT != pstCurPdpEntityFsmCtx->stSubFsm.enFsmId)
        {

            enPreSubFsmId = pstCurPdpEntityFsmCtx->stSubFsm.enFsmId;

            stPriFsmInfo.enFsmId = pstCurPdpEntityFsmCtx->stSubFsm.enFsmId;
            stPriFsmInfo.ulState = pstCurPdpEntityFsmCtx->stSubFsm.ulState;

            ulRet     = TAF_APS_FSM_ProcessEvent( pstCurPdpEntityFsmCtx->stSubFsm.ulState,
                                                  ulEventType,
                                                  (VOS_VOID*)pstMsg,
                                                  pstCurPdpEntityFsmCtx->stSubFsm.pstFsmDesc );
            /* ��ǰ��״̬����������仯�����Ҳ����˳���״̬����
              ˵����������״̬���л�����Ҫ�ٴν��뵽״̬������������ */
            if ( (TAF_APS_FSM_BUTT != pstCurPdpEntityFsmCtx->stSubFsm.enFsmId )
               &&( enPreSubFsmId != pstCurPdpEntityFsmCtx->stSubFsm.enFsmId ) )
            {
                ulRet     = TAF_APS_FSM_ProcessEvent( pstCurPdpEntityFsmCtx->stSubFsm.ulState,
                                                      ulEventType,
                                                      (VOS_VOID*)pstMsg,
                                                      pstCurPdpEntityFsmCtx->stSubFsm.pstFsmDesc );
            }

            stCurrFsmInfo.enFsmId = pstCurPdpEntityFsmCtx->stSubFsm.enFsmId;
            stCurrFsmInfo.ulState = pstCurPdpEntityFsmCtx->stSubFsm.ulState;

        }
        else
        {
            stPriFsmInfo.enFsmId = pstCurPdpEntityFsmCtx->stMainFsm.enFsmId;
            stPriFsmInfo.ulState = pstCurPdpEntityFsmCtx->stMainFsm.ulState;

            /* ������״̬��������Ϣ���� */
            ulRet     = TAF_APS_FSM_ProcessEvent( pstCurPdpEntityFsmCtx->stMainFsm.ulState,
                                                  ulEventType,
                                                  (VOS_VOID*)pstMsg,
                                                  pstCurPdpEntityFsmCtx->stMainFsm.pstFsmDesc );
            if (VOS_TRUE == ulRet)
            {
                /* �����ǰ��״̬���Ѿ������˴��������Ҵ�ʱ��״̬�����ڣ�˵����״̬״̬��
                   ���������У���������״̬�����ٴν��뵽��״̬�����д��� */
                if (TAF_APS_FSM_BUTT != pstCurPdpEntityFsmCtx->stSubFsm.enFsmId)
                {
                    /* ��Ϣ���� */
                    ulRet     = TAF_APS_FSM_ProcessEvent( pstCurPdpEntityFsmCtx->stSubFsm.ulState,
                                                          ulEventType,
                                                          (VOS_VOID*)pstMsg,
                                                          pstCurPdpEntityFsmCtx->stSubFsm.pstFsmDesc );
                }

            }

            stCurrFsmInfo.enFsmId = pstCurPdpEntityFsmCtx->stSubFsm.enFsmId;
            stCurrFsmInfo.ulState = pstCurPdpEntityFsmCtx->stSubFsm.ulState;
        }

        /* ��ά�ɲ⣬��ӡ������Ϣǰ���״̬����Ϣ */
        TAF_APS_LogFsmMntnInfo(&stPriFsmInfo, &stCurrFsmInfo);
    }

    return ulRet;
}

/*****************************************************************************
 �� �� ��  : TAF_APS_BuildEventType
 ��������  : ����EventType
 �������  : ulEventType :  ��Ϣ����+PID
              pMsg        :  ��Ϣ����
 �������  : ��
 �� �� ֵ  : ulEventType�¼�����
 ���ú���  :
 ��������  :

 �޸���ʷ      :
  1.��    ��   : 2011��12��16��
    ��    ��   : h44270
    �޸�����   : �����ɺ���

  2.��    ��   : 2015��6��6��
    ��    ��   : l00198894
    �޸�����   : Modem PID��չ
*****************************************************************************/
VOS_UINT32 TAF_APS_BuildEventType(
    struct MsgCB                       *pstMsg
)
{
    MSG_HEADER_STRU                    *pstMsgHeader;
    REL_TIMER_MSG                      *pstRcvTimerMsg;
    VOS_UINT32                          ulEventType = 0;
    APS_SNDCP_COMMON_MSG               *pstSnCommonMsg;

    /*
       ���������ʱ����Ϣ���ܿ���Ϣͷ���ƽ������֣�������ṹ���ulName���������
       ���Դ˴����зֱ���
    */
    pstMsgHeader = (MSG_HEADER_STRU*)pstMsg;
    if ( VOS_PID_TIMER == pstMsgHeader->ulSenderPid )
    {
        pstRcvTimerMsg = (REL_TIMER_MSG *)pstMsg;

        ulEventType  = TAF_BuildEventType(pstMsgHeader->ulSenderPid, pstRcvTimerMsg->ulName);

    }
    else if (WUEPS_PID_SM == pstMsgHeader->ulSenderPid)
    {
        ulEventType = TAF_BuildEventType(pstMsgHeader->ulSenderPid, pstMsgHeader->ulMsgName);
    }
    else if (UEPS_PID_SN == pstMsgHeader->ulSenderPid)
    {
        /* SNDCP�ĸ�ʽ��Ҳ��Ҫ���⴦��һ�£�msgname�ĳ��Ȳ�ͬ */
        pstSnCommonMsg = (APS_SNDCP_COMMON_MSG*)pstMsg;
        ulEventType = TAF_BuildEventType(pstMsgHeader->ulSenderPid, pstSnCommonMsg->usMsgType);
    }
    else
    {
        ulEventType = TAF_BuildEventType(pstMsgHeader->ulSenderPid, pstMsgHeader->ulMsgName);
    }

    return ulEventType;
}

/*****************************************************************************
 �� �� ��  : TAF_APS_ProcMsgEntry
 ��������  : APS����Ϣ�������������
 �������  : pstMsg : ����������Ϣ
 �������  : ��
 �� �� ֵ  :
 ���ú���  :
 ��������  :

 �޸���ʷ      :
 1.��    ��   : 2011��12��27��
   ��    ��   : h44270
   �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID  TAF_APS_ProcMsgEntry(
    struct MsgCB                       *pstMsg
)
{
    VOS_UINT32                          ulRet;
    VOS_UINT32                          ulEventType;
    REL_TIMER_MSG                      *pstRcvTimerMsg;


    if ( VOS_NULL_PTR == pstMsg )
    {
        TAF_ERROR_LOG(WUEPS_PID_TAF,"TAF_APS_ProcMsgEntry:null pointer");
        return;
    }

    /* ����ǳ�ʱ��Ϣ����Ҫ��ʽ�������ʱ��������״̬ */
    if ( VOS_PID_TIMER == ((MSG_HEADER_STRU*)pstMsg)->ulSenderPid )
    {
        pstRcvTimerMsg = (REL_TIMER_MSG *)pstMsg;

        TAF_APS_StopTimer(pstRcvTimerMsg->ulName, pstRcvTimerMsg->ulPara);
    }

    /*
       �����������Ϣ�����������շ����ߵ�PID����Ϣ�������֣����߹�ͬ
       ����EventType
    */
    ulEventType = TAF_APS_BuildEventType(pstMsg);


    /* �����Ԥ�������Ѿ����������ֱ�ӷ��� */
    if ( VOS_TRUE == TAF_APS_PreProcessMsg(ulEventType, pstMsg))
    {
        return;
    }

    /* ����״̬������ */
    ulRet  = TAF_APS_ProcessMsgInFsm(ulEventType, pstMsg);

    /* �˴��������е����⣬��Ҫ�����ж���ֻ����״̬�����˳���ʱ��
       ����Ҫ�������� */

    /* ����Ϣ��״̬�����Ѿ��������,�ɳ��Դ���һ�»��� */
    if ( VOS_TRUE == ulRet)
    {
        TAF_APS_ProcessBufferMsg(ulEventType, pstMsg);
    }
    /* �ڵ�ǰ״̬����δ������ϣ��ж���Ϣ�Ƿ���Ҫ��ϵ�ǰ��L2״̬��,���� */
    else
    {
        TAF_APS_PostProcessMsg(ulEventType, pstMsg);
    }

    return;

}

/*****************************************************************************
 �� �� ��  : TAF_APS_ProcMsg
 ��������  : APS����Ϣ��������
 �������  : pstMsg : APS�յ�����Ϣ
 �������  : ��
 �� �� ֵ  :
 ���ú���  :
 ��������  :

 �޸���ʷ      :
 1.��    ��   : 2011��12��16��
   ��    ��   : h44270
   �޸�����   : �����ɺ���

*****************************************************************************/
VOS_VOID  TAF_APS_ProcMsg(
    struct MsgCB                       *pstMsg
)
{
    TAF_APS_INTERNAL_MSG_BUF_STRU      *pstNextMsg;

    /* �ȴ����ⲿ��Ϣ */
    TAF_APS_ProcMsgEntry(pstMsg);

    /* �ⲿ��Ϣ������ɺ����ڲ���Ϣ */
    pstNextMsg = TAF_APS_GetNextInternalMsg();

    while (VOS_NULL_PTR != pstNextMsg)
    {

        /* ������Ϣ������,�Ա�����PSTAS����ʾ */
        DIAG_TraceReport(pstNextMsg);
        TAF_APS_ProcMsgEntry((struct MsgCB *)pstNextMsg);

        /* Ѱ����һ���ڲ���Ϣ */
        pstNextMsg = TAF_APS_GetNextInternalMsg();
    }

    return;
}

/*lint +e958*/


#ifdef __cplusplus
    #if __cplusplus
        }
    #endif
#endif


