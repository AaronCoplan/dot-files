;; User pack init file
;;
;; Use this file to initiate the pack configuration.
;; See README for more information.

;; Load bindings config
(live-load-config-file "bindings.el")

(setq-default c-basic-offset 8)
(add-hook 'java-mode-hook (lambda ()
                                (setq c-basic-offset 4)))

