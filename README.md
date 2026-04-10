# SMS UPS

Integração Home Assistant para nobreaks da marca SMS.

## Modelos compatíveis confirmados
- [SMS Pro 1500](https://www.sms.com.br/produtos/detalhe/nobreaks-ups-1/line-interactive/nobreak-sms-pro-1500-va/)
- SMS Pro 700

## Requerimentos

O nobreak deve estar conectado ao servidor do Home Assistant via cabo USB.

## Como instalar

### HACS

No canto superior direito clique no botão com 3 pontos e em [custom repositories](https://www.hacs.xyz/docs/faq/custom_repositories/). Cole o [link deste repositório](https://github.com/billbatista/sms-ups) e selecione a opção `Integration` e clique em `Add`. Reinicie o Home Assistant.


### Manualmente

[Baixe](https://github.com/billbatista/sms-ups/archive/refs/heads/main.zip) o repositório, copie e cole a pasta `sms-ups` que fica dentro de `custom_components` na pasta `config/custom_components` do Home Assistant. Reinicie o Home Assistant.

# Configuração

Depois de instalar vá à página de integrações do HA e procure por `sms ups`. A integração irá pedir o caminho da porta USB que o dispositivo está conectado, a potência total do seu modelo e fator de potência. Verifique por estes valores no manual do seu produto.

# Sensores disponíveis

|Nome|Detalhes|
|--|--|
|Alarm muted|Indica se o alarme sonoro do aparelho foi mutado|
|Battery level|Indica o nível de carga da bateria. Em meus testes, esta informação só é atualizada quando o nobreak está conectado à rede elétrica, ou seja, não é atualizado quando está no modo bateria|
|Input voltage|Tensão de entrada|
|Low battery|Bateria baixa|
|On battery|Nobreak está fornecendo energia através da bateria|
|Output frequency|Frequência de entrada|
|Output power|Potência de saída, levando em consideração a potência total do aparelho + fator de potência|
|Output voltage|Tensão de saída|
|Running test|Se algum teste está sendo executado no momento|
|Status|Status do aparelho|
|Temperatura|Temperatura ambiente do aparelho|

# Resolução de problemas

## Meu nobreak não aparece na lista de portas USB

Este problema varia de acordo com o método de instalação do HA que você utiliza (docker, máquina virtual, instalado direto no hardware). Procure por `usb passthrough` + seu método de instalação para entender como passar o USB conectado ao seu servidor para o HA.

# Reconhecimento

Esta integração só foi possível graças ao trabalho disponível em:
- https://github.com/cavamora/home_assistant_nodered_sms_ups_monitor/blob/main/README.md
- https://github.com/dmslabsbr/smsUps