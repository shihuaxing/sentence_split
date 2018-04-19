#!/usr/bin/env python3
#*--coding=utf-8--*
# 分析是句子(sent)还是段落(doc)
# 返回数据: src_type,句子列表
from collections import deque
class SrcType(object):
    '''
    判断文本是句子(sent)还是篇章(doc)
    判断的依据是长度和标点信息
    return: 如果是篇章 ('doc',[sent1,sent2])
            如果是句子 ('sent',[sent])

    '''
    punk = '.．。。！!！?？'.replace(' ','')
    punk_small = ',;，；'.replace(' ','')
    punk_patch = set('\'\"“”'.replace(' ',''))
    punk_list = set(list(punk))
    punk_small_list = set(list(punk_small))
    @classmethod
    def _detect(cls, src, punk_list):
        # 利用符号判断句子
        for i in punk_list:
            src = src.replace(i,i+'@#@punc@#@')
        sent_list = [sent.strip() for sent in src.split('@#@punc@#@')]
        if len(sent_list) == 1:
            return ('sent', sent_list)
        elif len(sent_list) > 1:
            return ('doc', sent_list)
        else:
            return ('error',[])
    @classmethod
    def detect1(cls, src):
        # 利用符号判断句子
        _punk = '.．。。！!！?？,;，；\'\"“”'.replace(' ','')
        _punk_list = set(list(_punk))
        for i in _punk_list:
            src = src.replace(i,i+'@#@punc@#@')
        parts_list = [sent.strip() for sent in src.split('@#@punc@#@') if len(sent) > 0]
        sent_list = []
        sent = []
        del src
        table = {'patch_flag': False,'fragments': 0, 'length':0}
        for index, parts in enumerate(parts_list):
            # 用最小分割来分割, 然后黏贴到句子缓冲中.通过判断黏贴后的句子的状态来决定是否存入结果列表
            # 判断的目标: 1,过长的句子要切分,2.引号中的句子不切分,3.多个标点联合在一起时,不切分,归属于上一个段
            # 判断是否句子过长
            sent.append(parts)
            table['fragments'] += 1
            table['length'] += len(parts)
            if table['length'] > 300:
                # 是否超长
                chunk_size = int(table['length']/3)+1  # 分成3段
                seprater_small = cls._detect(''.join(sent).strip(),cls.punk_small_list)  #按小标点切分
                if seprater_small[0] == 'doc':
                    # 是否可用小标点分割
                    sent_list.extend(seprater_small[1])
                else:
                    # 按长度切割
                    sent_list.extend([''.join(sent).strip()[i:i+chunk_size] for i in range(0, len(''.join(sent).strip()), chunk_size)])
                sent.clear()
                table = {'patch_flag': False,'fragments': 0, 'length':0}
            elif parts[-1] in cls.punk_patch:
                # 添加了一个引号,异或运算
                table['patch_flag'] = table['patch_flag']^True
 #               print('patch_flag:',parts,table['patch_flag'])
                if not table['patch_flag']:
                    # 如果引号已经封闭，并且引号的上一个字符是分割符号，则断句
                    try:
                        if sent[-2][-1] in cls.punk_list:
                            sent_list.append(''.join(sent).strip())
                            sent.clear()
                            table = {'patch_flag': False,'fragments': 0, 'length':0}
                    except IndexError:
                        pass
            elif parts[-1] in cls.punk_list:
                # 本段最后一个字是否在句号列表里
                try:
                    # 如果下一个字也在标点列表里说明这个标点不是结尾,向后跳转
                    if parts_list[index+1][0] in (cls.punk_list or cls.punk_small_list):
                        continue
                except:
                    pass
                if table['length'] <= 1:
                    # 单独的标点不切分
                    continue
                elif len(sent) >= 2:
                    if sent[-2][-1] in (cls.punk_list or cls.punk_small_list):
                        if len(''.join(sent)) < 10:
                        # 连续的标点不切分
                            continue
                else:
                    # sent列表此时只有当前段落
                    pass
                if not table['patch_flag']:
                    # 如果不在引号状态下, 清空句子缓存并存入句子列表
                    sent_list.append(''.join(sent).strip())
                    sent.clear()
                    table = {'patch_flag': False,'fragments': 0, 'length':0}
                else:
                    # 如果在引号状态下的句子太长,则可以分割
                    pass
                    if table['length'] > 140:
                        sent_list.append(''.join(sent).strip())
                        sent.clear()
                        table = {'patch_flag': False,'fragments': 0, 'length':0}
            else:
                pass
                #print (sent)
        if parts[-1] in cls.punk_list:
            # 将缓存中的字符串存入列表
            sent_list.append(''.join(sent).strip())
            sent.clear()
            table = {'patch_flag': False,'fragments': 0, 'length':0}
        if len(sent_list) == 1:
            # 单句
            print (len(sent_list))
            return ('sent', sent_list)
        elif len(sent_list) > 1:
            # 篇章
            print (len(sent_list))
            return ('doc', sent_list)
        else:
            print ('!!!err')
            return ('error',[])
    @classmethod
    def detect2(cls,src):
        # 利用符号判断句子, 在引号中间的句子不分割,
        # 引号下如果句长超过140依然按照句号切分
        # 如果整体句长超过300, 则自动切换成细粒度切分,即逗号,分号
        # 如果还分不开那么说明就是缺标点， 直接按长度140个一句话来切分
        #sent=deque()
        sent = []
        sent_list=[]
        patch_flag=False

        for index, _char in enumerate(src):
            sent.append(_char)
            if len(''.join(sent).strip())>300:
                # 是否超长没有标点
                seprater_small = cls._detect(''.join(sent).strip(),cls.punk_small_list)
                if seprater_small[0] == 'doc':
                    sent_list.extend(seprater_small[1])
                else:
                    sent_list.extend([''.join(sent).strip()[i:i+150] for i in range(0, len(''.join(sent).strip()), 150)])
                sent.clear()
                patch_flag=False
            elif _char in cls.punk_patch:
                # 是否是引号
                patch_flag=patch_flag^True
                if not patch_flag:
                    # 如果引号已经封闭，并且引号的上一个字符是分割符号，则断句
                    try:
                        if sent[-2] in cls.punk_list:
                            sent_list.append(''.join(sent).strip())
                            sent.clear()
                    except IndexError:
                        pass
            elif _char in cls.punk_list:
                # 是否在句号列表里
                try:
                    if src[index+1] in (cls.punk_list or cls.punk_small_list):
                        continue
                except:
                    pass
                if len(sent) <= 1:
                    # 连续的标点不切分
                    continue
                elif sent[-2] in (cls.punk_list or cls.punk_small_list):
                    if len(sent) < 10:
                    # 连续的标点不切分
                        continue
                if not patch_flag:
                    # 如果不在引号状态下, 清空句子缓存并存入句子列表
                    sent_list.append(''.join(sent).strip())
                    sent.clear()
                else:
                    # 如果在引号状态下的句子太长,则可以分割
                    if len(''.join(sent).strip()) > 140:
                        sent_list.append(''.join(sent).strip())
                        sent.clear()
                        patch_flag=False
        if len(sent) > 0:
            # 将缓存中的字符串存入列表
            sent_list.append(''.join(sent).strip())
            sent.clear()
        if len(sent_list) == 1:
            print (len(sent_list))
            return ('sent', sent_list)
        elif len(sent_list) > 1:
            print (len(sent_list))
            return ('doc', sent_list)
        else:
            print ('!!!err')
            return ('error',[])


if __name__=="__main__":
    import time,sys
    from line_profiler import LineProfiler

    with open(sys.argv[1]) as file1:
        c=file1.read().strip()
    t1=time.time()
    fileo1=open(sys.argv[1]+'.1','w')
#    fileo2=open(sys.argv[1]+'.2','w')
    for i in SrcType.detect1(c)[1]:
#        #print('===句长 %d ===' % len(i))
        print (i,file=fileo1)
#    for i in SrcType.detect2(c)[1]:
#        #print('===句长 %d ===' % len(i))
#        print (i,file=fileo2)
    fileo1.close()
#    fileo2.close()
    t2 = time.time()
    print (t2-t1)
 #   lp = LineProfiler()
 #   # lp.add_function(run1)
 ##   lp_wrapper = lp(SrcType._detect)
 ##   lp_wrapper(c,SrcType.punk_list)
 #   lp_wrapper = lp(SrcType.detect1)
 #   lp_wrapper(c)
 #   lp.print_stats()



