import fileinput
import optparse

names=open('/PATH/to/FILE/taxdump/names.dmp','r')
nodes=open('/PATH/to/FILE/taxdump/nodes.dmp','r')

def get_LCA_from_blast(blastlines,idthreshold):
    nms=[]
    threshold=[]
    ids=[]
    idps=[]
    lseqs=[]
    names=[]
    gap_mm=[]
##################sort lines by highest Nm score###########
    for line in blastlines:
        text=line.split()
        length=text[4]
        al_len=text[5]
        mm=text[6]
        gaps=text[8]
        iden=text[11]
        
        nm=max([int(length),int(al_len)])-int(iden)
        nms.append(nm)
     
    blastlines.sort(key=dict(zip(blastlines, nms)).get)
    nms.sort()
    threshold=nms[0]
#########################append tax ids with Nm score over 'threshold'#################
    for line,nm in zip(blastlines,nms):
        text=line.split()
        length=text[4]
        mm=text[6]
        gaps=text[8]
        idp=round((float(length)-(float(nm)))*100/float(length),2)
        taxid=text[1].split('|')[0]
        
        if nm>threshold:
            break
        ids.append(taxid)
        names.append(text[1])
        gap_mm.append('_'.join([gaps,mm,length]))
        idps.append(str(idp))
        
    if not all([i==idps[0] for i in idps]):
        idps.append('NOT_ALL_MATCH')
####################find LCA if more than 1 id has been accepted################ 
    try:
        lca_id=taxidlist2LCA(ids)
        lca=':'.join(find_parents_w_rank_short(lca_id)).replace(' ','_')
    except:
        lca='NOMATCH_TAXID_NOT_FOUND'
        lca_id='NOT_FOUND'
    
    nm=nms[0]/float(length) 
    if (nm>(1-float(idthreshold))):#Similarity threshold set to "threshold" [default=95%]
        lca='NOMATCH_similarity_below_'+str(float(idthreshold)*100).replace('.0','')+'%'+lca
        lca_id='NOT_FOUND'
    
################## Assign to higher order taxa based on ID-percent thresholds (limits) ################
    drop='Not_dropped'
    limits=[98,95,90]
    i=float(idps[0])
    if 'NOMATCH' not in lca and limits[0]>i>=limits[2]:
        
        which_drop=[limits[0]>i>=limits[1],limits[1]>i>=limits[2]]
        drop_level=[i for i,j in zip(['genus','family'],which_drop) if j]
        drop='Dropped2'+drop_level[0]+lca.split(';')[0]
        lca=':'.join(drop_to_level(lca_id,drop_level[0]))
   
##################output line###############  
    stats='tothits:'+str(len(blastlines))+'_accepted-hits:'+str(len(ids))+'_Min-Nm:'+str(nms[0])+'_IDp:'+str(idps[0])
    return('\t'.join([text[0],lca,get_rank(lca_id).replace(' ','_'),':'.join(set(ids)),stats,length,':'.join(set(idps)),':'.join(set(gap_mm)),drop])+'\n')

################################################################################################


#########################    LOAD names.dmp and nodes.dmp INTO MEMORY    #######################


################################################################################################
name={}
id_from_name={}
parent={}
rank={}
gi2taxid={}
embl={}

lines_processed = 0
for line in names.readlines():
    lines_processed = lines_processed + 1
    if (lines_processed % 500000 == 0):
         print('names.dmp: processing line ' + str(lines_processed))
         
    text=line.replace('\t','').replace('\n','').split('|')
    text=text[0:4]
    
    id_from_name[text[1]]=text[0]
    if text[3]=='scientific name':
        name[text[0]]=text[1]
        

lines_processed = 0        
for line in nodes.readlines():
    lines_processed = lines_processed + 1
    if (lines_processed % 500000 == 0):
         print('nodes.dmp: processing line ' + str(lines_processed))
    text=line.replace('\t','').replace('\n','').split('|')
    parent[text[0]]=text[1]
    rank[text[0]]=text[2]
    embl[text[0]]=text[3]
    

################################################################################################


#########################    LCA FUNCTIONS    #######################


################################################################################################

def find_rankofparents(current_taxid):
    parents=[] 
    found = False
    while found == False:
        parents.append(rank[current_taxid])
        if (current_taxid == '1'):
            return(parents)
            found = True      
        else:
            current_taxid = parent[current_taxid]
def name1(taxid):
    textname=name[taxid]
    return(textname)
            
def get_rank(taxid):
    if taxid!='NOT_FOUND':
                
        try:
            rank1=rank[taxid]
        except:
            rank1='rank_not_found'
    else:
        rank1=taxid
    return(rank1)


def find_parents(current_taxid):
    # first look up the taxid for the species of interest
    parents=[] 
    # use a while loop to continue searching until we find what we are looking for
    found = False
    while found == False:
        parents.append(current_taxid)
        # find the rank of the parent
        if (current_taxid == '1'):
            #print 'hej'
            return(parents)
            found = True      
        else:
            current_taxid = parent[current_taxid]

def find_parents_w_rank(current_taxid):
    a=find_parents(current_taxid)
    b=find_rankofparents(current_taxid)
    return([name[i]+';'+j for i,j in zip(a,b)])

def find_parents_w_rank_short(current_taxid):
    a=find_parents(current_taxid)
    b=find_rankofparents(current_taxid)
    output=[name[i]+';'+j for i,j in zip(a,b) if j in ['subspecies','species','genus','family','suborder','order','superorder','class']]
    
    if a[0]+';'+b[0] not in output:
        output=[name[a[0]]+';'+b[0]]+output
    return(output)

def find_parents_smartsort(current_taxid,org_name):
    a=find_parents(current_taxid)
    b=find_rankofparents(current_taxid)
    output=[]
    for rank in ['subspecies','species','genus','subfamily','family','suborder','order','superorder','class']:
        if rank in b:
            outputname=[name[i]+';'+j for i,j in zip(a,b) if j==rank]
            output.append(outputname[0])
        else:
            output.append('AA;'+rank)

    output.append(org_name)
    return(output)

def drop_to_level(taxid,level):
    
    newname=[i.split(';')[0] for i in find_parents_w_rank(taxid) if i.split(';')[1]==level]
    try:
        new_taxid=id_from_name[newname[0]]
        return(find_parents_w_rank_short(new_taxid))
    except:
        return(find_parents_w_rank_short(taxid))

    

def find_LCA(taxid1,taxid2):
    for i in find_parents(taxid1):
        if i in find_parents(taxid2):
            return(i)
            break

def taxidlist2LCA(taxid_list2):
    count=0
    prev_LCA_id=[]
    taxid_list=[i for i in taxid_list2 if 'TAXID_NOT_FOUND' not in i]
    for taxid in taxid_list:
        count+=1
        
        if count==1:
            prev_LCA_id=taxid
            continue

        else:
            
            try:
                prev_LCA_id=find_LCA(taxid,prev_LCA_id)
            except:
                continue
    return(prev_LCA_id)

def smartsort(getLCA_lines):
    parents=[]
    for line in getLCA_lines:
        name=line.split()[1].split(';')[0].replace('_',' ')
        if '%' in name:
            name=name.split('%')[1]
        try:
            taxid=id_from_name[name]
        except:
            taxid='NOT_FOUND'
        try:
            parents.append(find_parents_smartsort(taxid,line))
        except:
            parents.append(['AA','AA','AA','AA','AA','AA','AA','AA','AA',line])


    l3=sorted(parents, key = lambda x: (x[8],x[7],x[6],x[5],x[4],x[3],x[2],x[1],x[0]))
    l4=[i[9] for i in l3]
    return(l4)

################################################################################################


#########################    MAIN PROGRAM    #######################


################################################################################################
def main():
############################ Import arguments ##############    
    p = optparse.OptionParser()
    p.add_option('--ignoretaxid', '-i',dest="wrongtax",help="csv file of taxids to ignore, first column should contain taxids")
    p.add_option("-t", "--threshold", dest="threshold", default=0.95, help="Ignores reads where the best alignment has less than a certain percentage identity to the refenrence [default=0.95]")
    options, arguments = p.parse_args()
    infiles=arguments
    
    #print options.length	
    print 'Identity threshold: '+str(options.threshold)
    
    #Open file defining taxids to ingore and store them as a list
    with open(options.wrongtax) as file:
        wrong_tax = [line.split(';')[0].split(',')[0].strip() for line in file]
    wrong_tax=[i for i in wrong_tax if not any(c.isalpha() for c in i)]
    
    #TAXIDS to ignore:
    #'155900'] Hansen, Willerslev et al Diverse animal records
    #1749399' Molecular analysis of vertebrates and plants in leopard cat (Prionailurus bengalensis) scat in southwest China
    #'37029' Prionailurus bengalensis == Sus scrofa
    #Taxid: 32644. GI:'FR873673.1'. UNID rat. Molecular analysis of vertebrates and plants in leopard cat (Prionailurus bengalensis) scat in southwest China
    #419950: Phascolosoma esculenta Exact same seq as Bos taurus
    #TAXID: 547489. GI: JN317319.1. Antibiotic resistance is ancient. Lagopus
    #32546=Dasyurus spartacus, 9280=Dasyurus hallucatus, 32545=Dasyurus albopunctatus
    
    #add taxids that should always be ignored
    [wrong_tax.append(taxid) for taxid in ['1749399','155900','37029','32644','419950','547489']]
    
    outlines=[]
############################ Loop over input files ##############
    
    prev_name=[]
    prev_text=[]
    
    for infile in infiles:

        outfile=infile.replace('.blast','')+'.getLCA.tsv'
        print '\nWriting to: '+outfile
        infile=open(infile,'r')
        outfile=open(outfile,'w')
        count_total=0
        
############################ loop over line in samfile ##############        
        for line in infile.readlines():
            
            text=line.split()
############################ find LCA from all lines with the same sequence identifier (field #1 in samfile) ##############   
            if text[0]!=prev_name and count_total!=0:
                lines2=[line2 for line2 in lines if line2.split()[1].split('|')[0] not in wrong_tax]

                if len(lines2)>0:
                    outlines.append(get_LCA_from_blast(lines2,options.threshold))
                else:
                    outlines.append(lines[0].split()[0]+'\tNOMATCH_all_taxids_ignored\t\t\t\t\t\t\t\n')
                
                count_total=0
                #break
            
            if count_total==0:
    
                prev_name=text[0]
                prev_text=text
                lines=[]
                lines2=[]
            lines.append(line)
            count_total+=1
        if 'lines' in locals():
            
            lines2=[line2 for line2 in lines if line2.split()[1].split('|')[0] not in wrong_tax]
            outlines.append(get_LCA_from_blast(lines2,options.threshold))

############################ Sort output lines and print to file ############            
        [outfile.write(i) for i in smartsort(outlines)]
        outfile.close()
           
        
    
if __name__ == '__main__':
    main() 
