/******************************************************************************

                  版权所有 (C), 2001-2011, 华为技术有限公司

 ******************************************************************************
  文 件 名   : IpsMntnCCore.h
  版 本 号   : 初稿
  作    者   : caikai
  生成日期   : 2013年7月23日
  最近修改   :
  功能描述   : IPS MNTN模块头文件
  函数列表   :
  修改历史   :
  1.日    期   : 2013年7月16日
    作    者   : caikai
    修改内容   : 创建文件

******************************************************************************/

#ifndef __IPSMNTNCCORE_H__
#define __IPSMNTNCCORE_H__

#ifdef __cplusplus
#if __cplusplus
extern "C" {
#endif
#endif

/*****************************************************************************
  1 其他头文件包含
*****************************************************************************/
#include "TTFComm.h"

#if (FEATURE_ON == FEATURE_IMS)
#include "ImsNicInterface.h"
#include "ImsNic.h"
#include "TtfOamInterface.h"

#include "tcpip/tcpip.h"
#include "tcpip/tcpip_ipv6.h"

#include "tcpip/public/arith_cbb/include/mbuf.h"
#include "tcpip/public/arith_cbb/include/utlsll.h"

#include "common/ipos/tcpip_ir/tcpip_ir.h"


#pragma pack(4)

/*****************************************************************************
  2 宏定义
*****************************************************************************/

#define IPS_MNTN_CCORE_INFO_LEN                 (10000)           /*TCP/IP协议栈基础信息最长长度*/

#define IPS_MNTN_CCORE_INFO_TYPE_LEN            (2)
#define IPS_MNTN_CCORE_INFO_TYPE_OFFSET         (4)               /*TCP/IP协议栈基础信息类型偏移*/
#define IPS_MNTN_CCORE_INFO_LEN_OFFSET          (4)               /*TCP/IP协议栈基础信息长度偏移*/

#define IPS_MNTN_CCORE_OK                       (0)
#define IPS_MNTN_CCORE_ERROR                    (-1)

#define IPS_CCORE_IFNAMSIZ                      (16)                    /*虚拟网卡名称长度*/
#define IPS_CCORE_END_NAME                      (8)
#define IPS_CCORE_APP_CMD_INFO_LEN              (256)                   /*捕获APP控制命令的最长长度*/
#define IPS_MNTN_CCORE_TRACE_MAX_BYTE_LEN       (3000)                  /*捕获TCP/IP协议栈报文最长长度 */
#define IPS_MNTN_CCORE_NAT_MAPPING_INFO_LEN     (40)                    /*捕获TCP/IP协议栈NAT映射信息基本长度*/
#define IPS_ARRAY_SIZE(x)                       (sizeof(x) / sizeof(x[0]))

#define IPS_MNTN_CCORE_LINK_LAYER_UP_MASK       (1)                     /* 链路层上行抓包标志 */
#define IPS_MNTN_CCORE_LINK_LAYER_DOWN_MASK     (1 << 1)                /* 链路层下行抓包标志 */
#define IPS_MNTN_CCORE_IPV4_CAPTRURE_UP_MASK    (1 << 2)                /* IPV4类型上行抓包标志 */
#define IPS_MNTN_CCORE_IPV4_CAPTRURE_DOWN_MASK  (1 << 3)                /* IPV4类型下行抓包标志 */
#define IPS_MNTN_CCORE_IPV6_CAPTRURE_UP_MASK    (1 << 4)                /* IPV6类型上行抓包标志 */
#define IPS_MNTN_CCORE_IPV6_CAPTRURE_DOWN_MASK  (1 << 5)                /* IPV6类型下行抓包标志 */
#define ARRAY_SIZE(x)                           (sizeof(x) / sizeof(struct x))                  /* 计算数组成员个数 */
#define IPS_MNTN_CCORE_LINK_UP_TYPE             (0)                    /* 链路层抓包类型上行 */
#define IPS_MNTN_CCORE_LINK_DOWN_TYPE           (1)                    /* 链路层抓包类型上行 */
#define IPS_MNTN_CCORE_MAX_IPV4_ADDR_NUM        (100)                  /* 能上报OM的最大IPV4地址数量 */
#define IPS_MNTN_CCORE_BASE_INFO_OFFSET_LEN     (12)                   /* 基本信息头长度 */


/* VISP定义IP类型 */
#ifndef IPPROTO_HOPOPTS
#define IPPROTO_HOPOPTS     0        /* 逐跳选项头  Hop-by-hop option header */
#endif
#ifndef IPPROTO_ICMP
#define    IPPROTO_ICMP     1        /* 控制报文协议 control message protocol */
#endif
#ifndef IPPROTO_IGMP
#define    IPPROTO_IGMP     2        /* 组管理协议 group mgmt protocol */
#endif
#ifndef IPPROTO_GGP
#define    IPPROTO_GGP      3       /* 路由 gateway^2 (deprecated) */
#endif
#ifndef IPPROTO_IPIP                /* IP协议上的IP ip over ip protocol */
#define IPPROTO_IPIP        4
#endif
#ifndef IPPROTO_TCP
#define    IPPROTO_TCP      6       /* 控制传输协议 tcp */
#endif
#ifndef IPPROTO_EGP
#define    IPPROTO_EGP      8       /* 外部路由协议 exterior gateway protocol */
#endif
#ifndef IPPROTO_PUP
#define    IPPROTO_PUP      12        /* pup */
#endif
#ifndef IPPROTO_UDP
#define    IPPROTO_UDP      17         /* user datagram protocol */
#endif
#ifndef IPPROTO_IDP
#define    IPPROTO_IDP      22        /* xns idp */
#endif
#ifndef IPPROTO_TP
#define    IPPROTO_TP       29         /* tp-4等级协商 tp-4 w/ class negotiation */
#endif
#ifndef IPPROTO_IPV6
#define IPPROTO_IPV6        41           /* 协议版本号6 IPv6 in IPv6 */
#endif
#ifndef IPPROTO_ROUTING
#define IPPROTO_ROUTING     43          /* 选路 IPv6 Routing header */
#endif
#ifndef IPPROTO_FRAGMENT
#define IPPROTO_FRAGMENT    44          /* IPv6 Fragmentation header */
#endif
#ifndef IPPROTO_GRE
#define    IPPROTO_GRE      47        /* 常规路由封装协议 Generic Route Encapsulation Protocol */
#endif
#ifndef IPPROTO_ESP
#define IPPROTO_ESP         50       /* IP数据 Ip Sec */
#endif
#ifndef IPPROTO_AH
#define IPPROTO_AH          51       /* IP数据 Ip Sec */
#endif
#ifndef IPPROTO_ICMPV6
#define IPPROTO_ICMPV6      58      /* 控制报文协议 ICMP6 */
#endif
#ifndef IPPROTO_NONE
#define IPPROTO_NONE        59      /* IP无下一项 IPv6 No next header */
#endif
#ifndef IPPROTO_DSTOPTS
#define IPPROTO_DSTOPTS     60      /* IP目的地址 IPv6 Destination header */
#endif
#ifndef IPPROTO_EON
#define    IPPROTO_EON      80        /* ISO cnlp */
#endif
#ifndef   IPPROTO_OSPF
#define    IPPROTO_OSPF     89        /* ISO cnlp */
#endif
#ifndef IPPROTO_ENCAP
#define    IPPROTO_ENCAP    98        /* encapsulation header */
#endif
#ifndef IPPROTO_VRRP
#define    IPPROTO_VRRP     112        /*  VRRP */
#endif
#ifndef IPPROTO_MAX
#define    IPPROTO_MAX      256
#endif
#ifndef IPPROTO_DONE
#define IPPROTO_DONE        257     /* 标志扩展头和上层协议处理结束 */
#endif

/* 能上报OM的最大IPV6路由条数 */
#define IPS_MNTN_CCORE_MAX_IPV6_ROUTE_ITEM              \
    (IPS_MNTN_CCORE_INFO_LEN / (IPS_MNTN_CCORE_BASE_INFO_OFFSET_LEN + sizeof(TCPIP_RT6_ENTRY_S)))

/* 能上报OM的最大IPV4路由条数 */
#define IPS_MNTN_CCORE_MAX_IPV4_ROUTE_ITEM              \
    (IPS_MNTN_CCORE_INFO_LEN / (IPS_MNTN_CCORE_BASE_INFO_OFFSET_LEN + sizeof(TCPIP_RT4_ENTRY_S)))

/*填充消息头*/
#define IPS_CCORE_FILL_MSG_HEADER(pSendMsg, RecvPid)    \
        (pSendMsg)->ulReceiverCpuId  = VOS_LOCAL_CPUID; \
        (pSendMsg)->ulReceiverPid    = RecvPid;

#define IPS_CCORE_OM_TRANS_DATA_OFFSET_LEN        /*lint -e(545) -e(413)*/(sizeof(DIAG_TRANS_IND_STRU))

#define IPS_CCORE_PKT_INFO_OFFSET_LEN             /*lint -e(545) -e(413)*/(offsetof(IPS_MNTN_CCORE_PKT_INFO_STRU, aucData))

#define IPS_CCORE_BRIDGE_PKT_INFO_OFFSET_LEN      /*lint -e(545) -e(413)*/(offsetof(IPS_MNTN_CCORE_BRIDGE_PKT_INFO_STRU, aucData))

#define IPS_CCORE_APP_CMD_INFO_OFFSET_LEN         /*lint -e(545) -e(413)*/(offsetof(IPS_MNTN_CCORE_APP_CMD_INFO_STRU, aucData))

#define IPS_CCORE_INFO_LEN                      (IPS_CCORE_OM_TRANS_DATA_OFFSET_LEN + IPS_MNTN_CCORE_INFO_LEN)

/*****************************************************************************
  3 枚举定义
*****************************************************************************/
enum IPS_MNTN_CCORE_TIMER_NAME_ENUM
{
    IPS_MNTN_CCORE_INFO_TIMER                 = 0x00000001,           /*周期性捕获TCP/IP协议栈基础信息定时器*/

    IPS_MNTN_CCORE_TIMER_NAME_BUTT
};
typedef VOS_UINT32 IPS_MNTN_CCORE_TIMER_NAME_ENUM_UINT32;

/*TCP/IP协议栈基础信息类型*/
enum IPS_MNTN_CCORE_BASE_INFO_ENUM
{
    ID_IPS_MNTN_CCORE_NETIF_INFO              = 0x1001,               /* 虚拟网卡信息 */
    ID_IPS_MNTN_CCORE_TCP_INFO                = 0x1002,               /* TCP网络连接信息 */
    ID_IPS_MNTN_CCORE_UDP_INFO                = 0x1003,               /* UDP网络连接信息 */
    ID_IPS_MNTN_CCORE_IPV4_ROUTE_INFO         = 0x1004,               /* IPV4路由信息 */
    ID_IPS_MNTN_CCORE_IPV6_ROUTE_INFO         = 0x1005,               /* IPV6路由信息 */
    ID_IPS_MNTN_CCORE_IPV4_ADDR_INFO          = 0x1006,               /* IPV4地址信息 */
    ID_IPS_MNTN_CCORE_IPV6_ADDR_INFO          = 0x1007,               /* IPV6地址信息 */

    ID_IPS_MNTN_CCORE_BASE_INFO_BUTT          = 0xffff
};
typedef unsigned short IPS_MNTN_CCORE_BASE_INFO_ENUM_UINT16;

/*TCP/IP协议栈基础信息类型*/
enum IPS_MNTN_CCORE_INFO_TYPE_ENUM
{
    ID_IPS_MNTN_CCORE_IFCONFIG_INFO           = 0x1001,               /*虚拟网卡信息*/
    ID_IPS_MNTN_CCORE_NETSTAT_ROUTES_INFO     = 0x1002,               /*路由信息*/
    ID_IPS_MNTN_CCORE_NETSTAT_ENTRIES_INFO    = 0x1003,               /*连接状态信息*/
    ID_IPS_MNTN_CCORE_NAT_RULES_INFO          = 0x1004,               /*NAT表规则信息*/
    ID_IPS_MNTN_CCORE_NAT_STATS_INFO          = 0x1005,               /*NAT表状态信息*/
    ID_IPS_MNTN_CCORE_NAT_PROXIES_INFO        = 0x1006,               /*NAT表协议信息*/
    ID_IPS_MNTN_CCORE_NAT_MAPPINGS_INFO       = 0x1007,               /*NAT表映射信息*/

    ID_IPS_MNTN_CCORE_NAT_TYPE_BUTT           = 0xffff
};
typedef unsigned short IPS_MNTN_CCORE_INFO_TYPE_ENUM_UINT16;

/* Interpeak可维可测回调函数下标指示 */
enum IPS_MNTN_CCORE_CB_TYPE_ENUM
{
    IPS_MNTN_CCORE_INPUT_DATA_CB        = 0,    /*TCP/IP可维可测接收报文*/
    IPS_MNTN_CCORE_OUTPUT_DATA_CB,              /*TCP/IP可维可测发送报文*/
    IPS_MNTN_CCORE_BRIDGE_DATA_CB,              /*TCP/IP网桥中转报文*/
    IPS_MNTN_CCORE_RECV_ARP_CB,                 /*TCP/IP协议栈接收的ARP控制报文*/
    IPS_MNTN_CCORE_SEND_ARP_CB,                 /*TCP/IP协议栈发送的ARP控制报文*/
    IPS_MNTN_CCORE_RECV_DHCPC_CB,               /*TCP/IP协议栈接收的DHCP控制报文*/
    IPS_MNTN_CCORE_SEND_DHCPC_CB,               /*TCP/IP协议栈发送的DHCP控制报文*/
    IPS_MNTN_CCORE_RECV_DHCPS_CB,               /*TCP/IP协议栈接收的DHCP控制报文*/
    IPS_MNTN_CCORE_SEND_DHCPS_CB,               /*TCP/IP协议栈发送的DHCP控制报文*/
    IPS_MNTN_CCORE_APP_CMD_CB,                  /*APP控制命令信息*/

    IPS_MNTN_CCORE_CB_TYPE_BUTT
};
typedef unsigned short  IPS_MNTN_CCORE_CB_TYPE_ENUM_UINT16;

/*****************************************************************************
  4 全局变量声明
*****************************************************************************/


/*****************************************************************************
  5 消息头定义
*****************************************************************************/


/*****************************************************************************
  6 消息定义
*****************************************************************************/


/*****************************************************************************
  7 STRUCT定义
*****************************************************************************/
#pragma pack(4)

/*****************************************************************************
 结构名    : IPS_MNTN_CCORE_CAPTURE_CB_PARA_STRU
 协议表格  :
 ASN.1描述 :
 结构说明  : Interpeak可维可测回调函数参数结构
*****************************************************************************/
typedef struct
{
    unsigned char      *paucNetIfName;  /* 虚拟网卡信息*/
    unsigned char      *paucSrcPort;    /* 发送虚拟网卡信息，网桥使用*/
    unsigned char      *paucDestPort;   /* 接受虚拟网卡信息，网桥使用*/
    unsigned char      *pucData;        /* 线性数据指针,内容为报文信息或者APP命令 */
    unsigned short      usLen;          /* 报文数据长度 */
    unsigned char       aucRsv[2];      /* 报文数据长度 */
}IPS_MNTN_CCORE_CAPTURE_PARA_STRU;

/*****************************************************************************
 结构名    : IPS_MNTN_CCORE_INFO_ENTITY
 结构说明  : 捕获TCP/IP协议栈基本信息实体
*****************************************************************************/
typedef struct
{
    HTIMER                                    hIpsMntnTimer;          /*定时器*/
    VOS_UINT32                                ulIpsMntnTimerLen;      /*定时器长度，固定1s*/
    IPS_MNTN_CCORE_INFO_ACTION_ENUM_UINT16    enIpsMntnFlag;          /*捕获TCP/IP协议栈基本信息开启标志*/
    VOS_UINT8                                 aucRsv[2];
}IPS_MNTN_CCORE_INFO_ENTITY;

/*****************************************************************************
 结构名    : IPS_MNTN_CCORE_PKT_INFO_STRU
 结构说明  : TCP/IP协议栈报文捕获
*****************************************************************************/
typedef struct
{
    VOS_UINT16                              usPrimId;
    VOS_UINT16                              usToolId;

    VOS_UINT8                               aucNetIfName[IPS_CCORE_IFNAMSIZ]; /* 虚拟网卡名称 */

    VOS_UINT16                              usLen;
    VOS_UINT8                               aucData[2];
} IPS_MNTN_CCORE_PKT_INFO_STRU;

/*****************************************************************************
 结构名    : IPS_MNTN_CCORE_BRIDGE_PKT_INFO_STRU
 结构说明  : 网桥中转报文捕获
*****************************************************************************/
typedef struct
{
    VOS_UINT16                              usPrimId;
    VOS_UINT16                              usToolId;

    VOS_UINT8                               aucSrcPort[IPS_CCORE_END_NAME];   /* 发送虚拟网卡信息 */
    VOS_UINT8                               aucDestPort[IPS_CCORE_END_NAME];  /* 接收虚拟网卡名称 */

    VOS_UINT16                              usLen;
    VOS_UINT8                               aucData[2];
} IPS_MNTN_CCORE_BRIDGE_PKT_INFO_STRU;

/*****************************************************************************
 结构名    : IPS_MNTN_CCORE_APP_CMD_INFO_STRU
 结构说明  : APP控制命令捕获
*****************************************************************************/
typedef struct
{
    VOS_UINT16                              usPrimId;
    VOS_UINT16                              usToolId;

    VOS_UINT16                              usLen;
    VOS_UINT8                               aucData[2];
} IPS_MNTN_CCORE_APP_CMD_INFO_STRU;

typedef VOS_UINT32 (*pfHookCb)(MBUF_S *pstMBuf);
typedef VOS_UINT32 (*pfRegHook)(VOS_UINT32 ulType, VOS_UINT32 ulPriority, pfHookCb pfHookCbFunc);
typedef VOS_UINT32 (*pfUnRegHook)(VOS_UINT32 ulType, pfHookCb pfHookCbFunc);

/*****************************************************************************
 结构名    : IPS_MNTN_CCORE_HOOK_MASK_OPS_STRU
 结构说明  : RTOSck平台可维可测接口钩子函数及掩码注册结构
*****************************************************************************/
typedef struct
{
    VOS_UINT32                              ulMask;
    VOS_UINT32                              ulType;
    VOS_UINT32                              ulPriority;
    pfHookCb                                pfHookCbFunc;
    pfRegHook                               pfRegHookFunc;
    pfUnRegHook                             pfUnRegHookFunc;
}IPS_MNTN_CCORE_HOOK_MASK_OPS_STRU;

/*****************************************************************************
  8 UNION定义
*****************************************************************************/


/*****************************************************************************
  9 OTHERS定义
*****************************************************************************/
extern IPS_MNTN_CCORE_TRACE_CONFIG_REQ_STRU          g_stIpsCcoreTraceMsgCfg;

/*****************************************************************************
  10 函数声明
*****************************************************************************/
extern VOS_VOID IPS_MNTN_CCORE_PktInfo
(
    VOS_UINT8                                    *pucPktData,
    VOS_UINT16                                    usPktLen,
    TTF_MNTN_MSG_TYPE_ENUM_UINT16                 usType
);
extern VOS_VOID IPS_MNTN_CCORE_IpsMntnInfoTimeoutProc(VOS_VOID);
extern VOS_VOID IPS_MNTN_CCORE_OutputIpsInfo
(
    VOS_UINT8                          *pucData,
    VOS_UINT16                          usType
);
extern VOS_VOID IPS_MNTN_CCORE_OutputIpsNatMappingsInfo
(
    VOS_UINT8                          *pucData
);
extern VOS_VOID IPS_MNTN_CCORE_OutputImsNicStatsInfo
(
    VOS_UINT8                          *pucData,
    VOS_UINT16                          usType
);
extern VOS_UINT32 IPS_MNTN_CCORE_GetPktLenByTraceCfg
(
    IPS_MNTN_CCORE_TRACE_CONFIG_STRU     *pstTraceCfg,
    VOS_UINT16                            usPktLen,
    VOS_UINT32                           *pulDataLen
);
extern VOS_VOID IPS_MNTN_CCORE_TransMsg
(
    VOS_UINT8                                       *pucTransMsg,
    VOS_UINT32                                       ulTransMsgContentLen,
    TTF_MNTN_MSG_TYPE_ENUM_UINT16                    enMsgName
);
extern VOS_UINT32 IPS_MNTN_CCORE_ReRegHooks(VOS_UINT32 ulMask);
extern VOS_VOID IPS_MNTN_CCORE_UnregHooks(VOS_UINT32 ulMask);
extern VOS_UINT32 IPS_MNTN_CCORE_RegHooks(VOS_UINT32 ulMask);
extern VOS_UINT32 IPS_MNTN_CCORE_IpLayerUpCapCB(MBUF_S *pMBuf);
extern VOS_UINT32 IPS_MNTN_CCORE_Ip6LayerUpCapCB(MBUF_S *pMBuf);
extern ULONG IPS_MNTN_CCORE_IpsecLayerDownCapCB(MBUF_S *pMBuf);
extern VOS_UINT32 IPS_MNTN_CCORE_IpLayerDownCapCB(MBUF_S *pMBuf);
extern VOS_UINT32 IPS_MNTN_CCORE_Ip6LayerDownCapCB(MBUF_S *pMBuf);
extern VOS_VOID IPS_MNTN_CCORE_OutputNetIfInfo(VOS_UINT8 *pucData, VOS_UINT16 usType);
extern VOS_VOID IPS_MNTN_CCORE_OutputUdpInfo(VOS_UINT8 *pucData, VOS_UINT16 usType);
extern VOS_VOID IPS_MNTN_CCORE_OutputTcpInfo(VOS_UINT8 *pucData, VOS_UINT16 usType);
extern VOS_VOID IPS_MNTN_CCORE_OutputRouteIpv4Info(VOS_UINT8 *pucData, VOS_UINT16 usType);
extern VOS_VOID IPS_MNTN_CCORE_OutputIpv4AddrInfo(VOS_UINT8 *pucData, VOS_UINT16 usType);
extern VOS_VOID IPS_MNTN_CCORE_PrintInfoCB(VOS_CHAR *pucData);
extern VOID IPS_MNTN_CCORE_TCPIP_FixlenLogOutput(ULONG ulLogCode, ULONG ulLogLevel, ULONG ulLogType, VOID *ucMessage,
                        ULONG ulPara1, ULONG ulPara2, ULONG ulPara3, ULONG ulPara4);
extern VOID IPS_MNTN_CCORE_TCPIP_VarlenLogOutput(ULONG ulLogCode, ULONG ulLogLevel,
                        ULONG ulLogType, VOID* pcFormat, VOID* pData);

#endif  /*FEATURE_ON == FEATURE_IMS*/

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

#endif /* end of IpsMntnCCore.h */



