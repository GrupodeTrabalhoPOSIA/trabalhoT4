import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import ChatComposer from './ChatComposer';

describe('ChatComposer', () => {
  it('envia com Enter no campo e limpa a mensagem', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ChatComposer onSubmit={onSubmit} />);
    const input = screen.getByLabelText('Sua pergunta');

    await user.type(input, 'Minha pergunta{Enter}');

    expect(onSubmit).toHaveBeenCalledExactlyOnceWith('Minha pergunta');
    expect(input).toHaveValue('');
  });

  it('insere uma nova linha com Shift+Enter sem enviar', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ChatComposer onSubmit={onSubmit} />);
    const input = screen.getByLabelText('Sua pergunta');

    await user.type(input, 'Primeira');
    await user.keyboard('{Shift>}{Enter}{/Shift}Segunda');

    expect(input).toHaveValue('Primeira\nSegunda');
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('não envia texto vazio nem apenas espaços', async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    render(<ChatComposer onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText('Sua pergunta'), '{Enter}   {Enter}');

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it.each([{ disabled: true }, { isSending: true }])(
    'não envia enquanto bloqueado: %j',
    async (props) => {
      const onSubmit = vi.fn();
      const user = userEvent.setup();
      const { rerender } = render(<ChatComposer onSubmit={onSubmit} />);
      const input = screen.getByLabelText('Sua pergunta');
      await user.type(input, 'Pergunta pendente');
      rerender(<ChatComposer onSubmit={onSubmit} {...props} />);

      fireEvent.keyDown(input, { key: 'Enter' });

      expect(onSubmit).not.toHaveBeenCalled();
      expect(input).toHaveValue('Pergunta pendente');
    },
  );

  it.each([{ isComposing: true }, { keyCode: 229 }, { repeat: true }])(
    'não envia ao confirmar composição ou repetir a tecla: %j',
    async (eventProps) => {
      const onSubmit = vi.fn();
      const user = userEvent.setup();
      render(<ChatComposer onSubmit={onSubmit} />);
      const input = screen.getByLabelText('Sua pergunta');
      await user.type(input, 'Pergunta');

      fireEvent.keyDown(input, { key: 'Enter', ...eventProps });

      expect(onSubmit).not.toHaveBeenCalled();
    },
  );
});
