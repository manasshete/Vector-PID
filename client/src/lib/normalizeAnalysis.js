/** Map Python pipeline JSON → React UI shape */
export function normalizeAnalysis(raw) {
  if (!raw) return null;

  const graph = raw.graph || {};
  const stats = {
    ...(raw.statistics || {}),
    graph_nodes: graph.num_nodes ?? raw.statistics?.graph_nodes ?? 0,
    graph_edges: graph.num_edges ?? raw.statistics?.graph_edges ?? 0,
    total_relationships:
      raw.statistics?.total_relationships ??
      raw.connections?.length ??
      raw.relationships?.length ??
      0,
  };

  const width = raw.drawing?.width ?? raw.drawing?.resolution?.width ?? 0;
  const height = raw.drawing?.height ?? raw.drawing?.resolution?.height ?? 0;

  const relationships = raw.connections || raw.relationships || [];

  return {
    drawing: {
      filename: raw.drawing?.filename ?? 'drawing',
      type: raw.drawing?.type ?? 'P&ID',
      resolution: { width, height },
      statistics: stats,
    },
    texts: raw.texts || [],
    objects: raw.objects || [],
    lines: raw.lines || [],
    relationships,
    graph,
    fullAnalysis: raw,
  };
}

export function normalizeSample(sample) {
  return normalizeAnalysis({
    drawing: {
      filename: sample.drawing.filename,
      type: sample.drawing.type,
      width: sample.drawing.resolution.width,
      height: sample.drawing.resolution.height,
    },
    statistics: sample.drawing.statistics,
    texts: sample.texts,
    objects: sample.objects,
    lines: sample.lines,
    connections: sample.relationships,
    graph: sample.graph,
  });
}
