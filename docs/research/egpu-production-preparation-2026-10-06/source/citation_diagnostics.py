"""Identify literal invalid citation fields; never choose or repair a citation."""
def feedback(error,arguments):
 if error!='citation has no selected fetched handle':return None
 doc=arguments.get('document',{});sources=doc.get('sources',[]);declared={x.get('source_handle') for x in sources if isinstance(x,dict) and isinstance(x.get('source_handle'),str)};invalid=[]
 for field in ['claims','disagreements']:
  for i,row in enumerate(doc.get(field,[])):
   if not isinstance(row,dict) or not isinstance(row.get('sources'),list):continue
   for j,value in enumerate(row['sources']):
    if isinstance(value,str) and value not in declared:invalid.append({'field_path':f'document.{field}[{i}].sources[{j}]','submitted_value':value,'read_id':value if value.startswith('read-') else None})
 if not invalid:return None
 return {'code':'citation_has_no_selected_fetched_handle','invalid_citation_fields':invalid,'declared_source_choices':[{'source_handle':x} for x in sorted(declared)],'recovery':'Every sources array in document.claims and document.disagreements takes an issued source_handle, never a read_id or URL. Only you select the supporting source. Correct your own explicit citation fields using actual delivered evidence. No value is chosen or rewritten for you. All original source, support, negative and quality gates remain.'}
def extend(base):
 class CitationDiagnosticEngine(base):
  def previous_rejection_feedback(self,error,arguments):
   original=super().previous_rejection_feedback(error,arguments)
   return original if original is not None else feedback(error,arguments)
 return CitationDiagnosticEngine
