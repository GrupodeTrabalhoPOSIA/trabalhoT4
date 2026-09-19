/** Static source documents: no backend or model call is needed to read T1–T3. */
export const sourceReports = {
  t1: {
    href: '/entregas/trabalho-01.pdf', label: 'Relatório original · PDF',
    original: 'Trabalho_01_Estudo_Comparativo_de_Modelos_e_Prompts_COMPLETO.docx (1).pdf',
    sha256: '2b017f073494efc4c36f3bfd6668f425d06844a79836e1375037c85ec0aa61d1',
  },
  t2: {
    href: '/entregas/trabalho-02.pdf', label: 'Relatório original · PDF',
    original: 'Trabalho_02_Especificação_Copiloto_e_Baseline_PREENCHIDO_completo.docx.pdf',
    sha256: '66cf58e4c7874bcd6ba03b760737471dfaeaaca3b67eec0d54e9f1124eb53f01',
  },
  t3: {
    href: '/entregas/trabalho-03.docx', label: 'Relatório original · DOCX',
    original: 'Trabalho_03_Relatorio.docx',
    sha256: '5005740662d7ad8c4ffc2524bc4fe70faed553085d8140d59041fe3fd53fe8f3',
  },
} as const;
